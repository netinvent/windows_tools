#! /usr/bin/env python
#  -*- coding: utf-8 -*-

# This file is part of windows_tools module

"""
windows server identification

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "windows_tools.server"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2021 Orsiris de Jong"
__description__ = "Windows server identification functions"
__licence__ = "BSD 3 Clause"
__version__ = "0.1.1"
__build__ = "2020040902"


import wmi


def is_windows_server():
    wmi_standard = wmi.WMI(namespace="cimv2")

    try:
        result = wmi_standard.Win32_OperatingSystem()[0].ProductType
        # ProductType 1 = Workstation, 2 = Domain Controller, 3 = Server
        # https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-operatingsystem
        if result in [2, 3]:
            return True
        return False
    except Exception:
        return None


def is_rds_server():
    """
    Check if current machine has terminal services in RDS or single user mode

    We'll first check Win32_OperatingSystem()[0].OSProductSuite
    Any result containing bit flag 256 means "Terminal Services is installed, but only one interactive session is supported"
    Any result containing bit flag 16 means "Terminal Services is installed"
    https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-operatingsystem


    With Win server 2008+, the new Win32_ServerFeature class provides info if RDS (id=18) is installed
    On older servers, we need to check if TerminelService service is running
    On clients, we need to exclude that check

    :return: boolean
    """
    wmi_standard = wmi.WMI(namespace="cimv2")

    try:
        result = wmi_standard.Win32_OperatingSystem()[0].OSProductSuite
        # Let's assume it's a client computer (or a server without RDS capabilities)
        # Might also be a server with RDS installed in admin mode (OSProductSuite=276)
        if result & 256:
            return False
        # TS installed and not multiple sessions forbidden
        if result & 16:
            return True
    except Exception:
        pass

    try:
        result = wmi_standard.Win32_ServerFeature(ID=18)
        if result == []:
            return False
        return True
    # Let's keep a very broad exception here because it would be a shame if install stops because of missing features
    except Exception:
        pass

    try:
        result = wmi_standard.Win32_TerminalService(State="Running")
        if result == []:
            return False
        return True
    except Exception:
        return None
