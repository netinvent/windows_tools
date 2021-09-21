#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
Get updates installed by Windows Update, including those the QFE doesn't list

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'windows_tools.updates'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2021 Orsiris de Jong'
__description__ = 'Windows user lookups for SID/PySID/Username'
__licence__ = 'BSD 3 Clause'
__version__ = '1.0.0'
__build__ = '2021092101'

import re

from win32com import client

OPERATION_CODES = {
    1: 'installation',
    2: 'uninstallation',
    3: 'other'
}

STATUS_CODES = {
    1: "in progress",
    2: "succeeded",
    3: "succeeded with errors",
    4: "failed",
    5: "aborted"
}


def get_windows_updates(update_path: str = "Microsoft.Update.Session",
                        filter_multiple: bool = False):
    """
    Search for Windows updates, including other products provided
    by Windows update, whereas qfe (Win32_quickfixEngineering) will
    only provide OS updates

    Original Technet article
    https://social.technet.microsoft.com/wiki/contents/articles/4197.windows-how-to-list-all-of-the-windows-and-software-updates-applied-to-a-computer.aspx

    Since antivirus updates will be the same KB, we add some possible duplicate filters
    """
    session = client.Dispatch(update_path)
    searcher = session.CreateUpdateSearcher()
    result = searcher.GetTotalHistoryCount()

    updates = []
    already_seen = []

    for entry in searcher.QueryHistory(0, result):
        update = {
            'kb': None,
            'date': entry.Date,
            'title': entry.Title,
            'description': entry.Description,
            'supporturl': entry.supportUrl,
            'operation': OPERATION_CODES[int(entry.Operation)],
            'result': STATUS_CODES[int(entry.ResultCode)],
        }

        # As of 2021, KB numbers go up to 7 digits
        kb = re.search(r'KB[0-9]{5,7}', entry.Title, re.IGNORECASE)
        try:
            update['kb'] = kb.group(0)
        except (IndexError, AttributeError):
            pass

        if filter_multiple:
            if update['kb']:
                if update['kb'] in already_seen:
                    continue
                already_seen.append(kb.group(0))
            # We don't have a match, let's use the title
            else:
                if entry.Title in already_seen:
                    continue
                already_seen.append(entry.Title)
        updates.append(update)

    return updates
