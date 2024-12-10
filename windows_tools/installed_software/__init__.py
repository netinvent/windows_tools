#! /usr/bin/env python
#  -*- coding: utf-8 -*-

# This file is part of windows_tools module

"""
List of installed software from Uninstall registry keys, 32 and 64 bits

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "windows_tools.installed_software"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2019-2024 Orsiris de Jong"
__description__ = "Get installed software from Uninstall registry keys, 32 and 64 bits"
__licence__ = "BSD 3 Clause"
__version__ = "0.5.4"
__build__ = "2021012601"

import windows_tools.registry


def get_installed_software() -> list:
    """
    Returns installed windows software found in registry

    :return: (list) List of dictionnaries containing name, version and publisher of software
    """
    software = []
    try:
        software = software + windows_tools.registry.get_values(
            hive=windows_tools.registry.HKEY_LOCAL_MACHINE,
            key=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            names=["DisplayName", "Publisher", "DisplayVersion"],
            arch=windows_tools.registry.KEY_WOW64_32KEY
            | windows_tools.registry.KEY_WOW64_64KEY,
            combine=True,
        )
    except FileNotFoundError:
        pass

    try:
        software = software + windows_tools.registry.get_values(
            hive=windows_tools.registry.HKEY_CURRENT_USER,
            key=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            names=["DisplayName", "Publisher", "DisplayVersion"],
            arch=windows_tools.registry.KEY_WOW64_32KEY
            | windows_tools.registry.KEY_WOW64_64KEY,
            combine=True,
        )
    except FileNotFoundError:
        pass

    # map dictionnary keys to actual used values
    for entry in software:
        try:
            entry["name"] = entry.pop("DisplayName")
        except KeyError:
            # Since we don't have a name, we cannot create an entry
            entry["name"] = ""
        try:
            entry["version"] = entry.pop("DisplayVersion")
        except KeyError:
            entry["version"] = ""
        try:
            entry["publisher"] = entry.pop("Publisher")
        except KeyError:
            entry["publisher"] = ""

    # Filter empty results
    return [
        soft
        for soft in software
        if soft != {"name": "", "version": "", "publisher": ""}
    ]
