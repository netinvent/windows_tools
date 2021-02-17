#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
Tool to run as another user

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'windows_tools.impersonate'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.1.3'
__build__ = '2021021601'

import pywintypes
import win32con
import win32security


class ImpersonateWin32Sec:
    """
    Allow to run some task as another user
    """
    def __init__(self, domain: str, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.domain = domain
        self.handle = None

    def __enter__(self) -> None:
        try:
            self.handle = win32security.LogonUser(self.username, self.domain, self.password,
                                                  win32con.LOGON32_LOGON_INTERACTIVE, win32con.LOGON32_PROVIDER_DEFAULT)
            win32security.ImpersonateLoggedOnUser(self.handle)
        except pywintypes.error as exc:
            raise OSError(exc)

    def __exit__(self, *args) -> None:
        try:
            win32security.RevertToSelf()
            self.handle.Close()
        except AttributeError:
            pass
