#! /usr/bin/env python
#  -*- coding: utf-8 -*-

# This file is part of windows_tools module

"""
Simple registry check for windows firewall status

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "windows_tools.windows_firewall"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020 Orsiris de Jong"
__description__ = "Windows firewall state retrieval"
__licence__ = "BSD 3 Clause"
__version__ = "0.1.1"
__build__ = "2020110201"

import windows_tools.registry


def is_firewall_active() -> bool:
    """
    Returns state of windows firewall

    :return: (bool)
    """
    try:
        fw_std = windows_tools.registry.get_value(
            windows_tools.registry.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile",
            "EnableFirewall",
        )
    except FileNotFoundError:
        fw_std = 0
    try:
        fw_dom = windows_tools.registry.get_value(
            windows_tools.registry.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile",
            "EnableFirewall",
        )
    except FileNotFoundError:
        fw_dom = 0
    try:
        fw_pub = windows_tools.registry.get_value(
            windows_tools.registry.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile",
            "EnableFirewall",
        )
    except FileNotFoundError:
        fw_pub = 0

    if fw_std == 1 or fw_dom == 1 or fw_pub == 1:
        return True
    return False
