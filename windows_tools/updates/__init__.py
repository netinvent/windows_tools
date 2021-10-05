#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
Get updates installed by Windows Update, via COM, WMI and registry paths, so we don't miss something on the list
See https://social.technet.microsoft.com/wiki/contents/articles/4197.windows-how-to-list-all-of-the-windows-and-software-updates-applied-to-a-computer.aspx

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "windows_tools.updates"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2021 Orsiris de Jong"
__description__ = (
    "Retrieve list of Windows Update installed updates including non-Windows Updates"
)
__licence__ = "BSD 3 Clause"
__version__ = "2.0.1"
__build__ = "2021100501"

import re
from win32com import client
import dateutil.parser
from windows_tools import wmi_queries
from windows_tools import registry


# As of 2021, KB numbers go up to 7 digits
KB_REGEX = re.compile(r"KB[0-9]{5,7}", re.IGNORECASE)


def get_windows_updates_wmi():
    """
    Search for Windows updates via WMI query in Win32_QuickFixEngineering
    """

    updates = []

    result = wmi_queries.query_wmi("SELECT * FROM Win32_QuickFixEngineering")
    for entry in result:
        # Since freaking windows WMI returns localized dates (thanks), we have to parse them to make sure
        # we have standard YYYY-MM-DD date formats
        parsedDate = dateutil.parser.parse(entry["InstalledOn"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        update = {
            "kb": entry["HotFixID"],
            "date": parsedDate,
            "title": None,
            "description": entry["Description"],
            "supporturl": entry["Caption"] if entry["Caption"] != "" else None,
            "operation": None,
            "result": None,
        }

        updates.append(update)

    return updates


def get_windows_updates_com(
    update_path: str = "Microsoft.Update.Session", filter_duplicates: bool = False
):
    """
    Search for Windows updates, including other products provided
    by Windows update, whereas qfe (Win32_quickfixEngineering) will
    only provide OS updates

    Original Technet article
    https://social.technet.microsoft.com/wiki/contents/articles/4197.windows-how-to-list-all-of-the-windows-and-software-updates-applied-to-a-computer.aspx

    Since antivirus updates will be the same KB, we add some possible duplicate filters
    """
    operation_codes = {1: "installation", 2: "uninstallation", 3: "other"}

    status_codes = {
        1: "in progress",
        2: "succeeded",
        3: "succeeded with errors",
        4: "failed",
        5: "aborted",
    }
    session = client.Dispatch(update_path)
    searcher = session.CreateUpdateSearcher()
    result = searcher.GetTotalHistoryCount()

    updates = []
    already_seen = []

    for entry in searcher.QueryHistory(0, result):
        update = {
            "kb": None,
            "date": entry.Date.strftime("%Y-%m-%d %H:%M:%S"),
            "title": entry.Title,
            "description": entry.Description,
            "supporturl": entry.supportUrl,
            "operation": operation_codes[int(entry.Operation)],
            "result": status_codes[int(entry.ResultCode)],
        }

        kb = KB_REGEX.search(entry.Title)
        try:
            update["kb"] = kb.group(0)
        except (IndexError, AttributeError):
            pass

        if filter_duplicates:
            if update["kb"]:
                if update["kb"] in already_seen:
                    continue
                already_seen.append(kb.group(0))
            # We don't have a match, let's use the title
            else:
                if entry.Title in already_seen:
                    continue
                already_seen.append(entry.Title)
        updates.append(update)

    return updates


def get_windows_updates_reg(
    reg_key: str = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\Packages",
    filter_duplicates: bool = True,
):
    """
    Search for windows updates via registry Key since WMI and COM methods aren't fully aware of every update
    Let's get the last modified date from registry as install date too

    We need to filter multiple times the same KB because it's
    """

    states = {
        0: "Absent",
        5: "Uninstall Pending",
        16: "Resolving",
        32: "Resolved",
        48: "Staging",
        64: "Staged",
        80: "Superseeded",
        96: "Install Pending",
        101: "Partially Installed",
        112: "Installed",
        128: "Permanent",
    }

    installed_states = [112, 128]

    keys = registry.get_values(
        hive=registry.HKEY_LOCAL_MACHINE,
        key=reg_key,
        names=["CurrentState", "InstallLocation"],
        last_modified=True,
    )
    updates = []
    already_seen = []

    for key in keys:
        update = {
            "kb": None,
            "date": key["InstallLocation"]["last_modified"],
            "title": None,
            "description": None,
            "supporturl": None,
            "operation": None,
            "result": None,
        }
        kb = KB_REGEX.search(key["InstallLocation"]["value"])
        try:
            update["kb"] = kb.group(0)
        except (IndexError, AttributeError):
            continue
        if filter_duplicates:
            if update["kb"]:
                if update["kb"] in already_seen:
                    continue
                already_seen.append(kb.group(0))
        if key["CurrentState"] in installed_states:
            updates.append(update)

    return updates


def get_windows_updates(filter_duplicates: bool = True):
    """
    Let's get windows updates from multiple sources

    COM method has most info
    WMI method has some info
    REG method has only install date and KB number info
    """
    wmi_update_list = get_windows_updates_wmi()
    com_update_list = get_windows_updates_com(filter_duplicates=filter_duplicates)
    reg_update_list = get_windows_updates_reg()

    updates = com_update_list
    if filter_duplicates:
        for wmi_update in wmi_update_list:
            dup = False
            for com_update in com_update_list:
                if wmi_update["kb"] == com_update["kb"]:
                    dup = True
            if dup:
                continue
            updates.append(wmi_update)
        for reg_update in reg_update_list:
            dup = False
            for com_update in com_update_list:
                if reg_update["kb"] == com_update["kb"]:
                    dup = True
            if dup:
                continue
            updates.append(reg_update)
    else:
        updates += wmi_update_list
        updates += reg_update_list
    return updates
