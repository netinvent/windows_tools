#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
Privilege enabling / disabling, raw copy from # https://stackoverflow.com/a/34710464/2635443

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'windows_tools.securityprivilege'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong / Eryk Sun https://stackoverflow.com/a/34710464/2635443'
__description__ = 'Privilege enable/disable functions'
__licence__ = 'BSD 3 Clause'
__version__ = '0.1.2'
__build__ = '2020102901'

import ctypes
from ctypes import wintypes

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)

ERROR_NOT_ALL_ASSIGNED = 0x0514
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ALL_ACCESS = 0x000F0000 | 0x01FF


class LUID(ctypes.Structure):
    _fields_ = (('LowPart', wintypes.DWORD),
                ('HighPart', wintypes.LONG))


class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = (('Luid', LUID),
                ('Attributes', wintypes.DWORD))


class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = (('PrivilegeCount', wintypes.DWORD),
                ('Privileges', LUID_AND_ATTRIBUTES * 1))

    def __init__(self, PrivilegeCount=1, *args):
        super(TOKEN_PRIVILEGES, self).__init__(PrivilegeCount, *args)


PDWORD = ctypes.POINTER(wintypes.DWORD)
PHANDLE = ctypes.POINTER(wintypes.HANDLE)
PLUID = ctypes.POINTER(LUID)
PTOKEN_PRIVILEGES = ctypes.POINTER(TOKEN_PRIVILEGES)


def errcheck_bool(result, func, args):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return args


kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)

kernel32.GetCurrentProcess.errcheck = errcheck_bool
kernel32.GetCurrentProcess.restype = wintypes.HANDLE

# https://msdn.microsoft.com/en-us/library/aa379295
advapi32.OpenProcessToken.errcheck = errcheck_bool
advapi32.OpenProcessToken.argtypes = (
    wintypes.HANDLE,  # _In_  ProcessHandle
    wintypes.DWORD,  # _In_  DesiredAccess
    PHANDLE)  # _Out_ TokenHandle

# https://msdn.microsoft.com/en-us/library/aa379180
advapi32.LookupPrivilegeValueW.errcheck = errcheck_bool
advapi32.LookupPrivilegeValueW.argtypes = (
    wintypes.LPCWSTR,  # _In_opt_ lpSystemName
    wintypes.LPCWSTR,  # _In_     lpName
    PLUID)  # _Out_    lpLuid

# https://msdn.microsoft.com/en-us/library/aa375202
advapi32.AdjustTokenPrivileges.errcheck = errcheck_bool
advapi32.AdjustTokenPrivileges.argtypes = (
    wintypes.HANDLE,  # _In_      TokenHandle
    wintypes.BOOL,  # _In_      DisableAllPrivileges
    PTOKEN_PRIVILEGES,  # _In_opt_  NewState
    wintypes.DWORD,  # _In_      BufferLength
    PTOKEN_PRIVILEGES,  # _Out_opt_ PreviousState
    PDWORD)  # _Out_opt_ ReturnLength


def enable_privilege(privilege) -> None:
    hToken = wintypes.HANDLE()
    luid = LUID()
    tp = TOKEN_PRIVILEGES()
    advapi32.LookupPrivilegeValueW(None, privilege, ctypes.byref(luid))
    tp.Privileges[0].Luid = luid
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
    advapi32.OpenProcessToken(kernel32.GetCurrentProcess(),
                              TOKEN_ALL_ACCESS,
                              ctypes.byref(hToken))
    try:
        advapi32.AdjustTokenPrivileges(hToken, False,
                                       ctypes.byref(tp),
                                       ctypes.sizeof(tp),
                                       None, None)
        if ctypes.get_last_error() == ERROR_NOT_ALL_ASSIGNED:
            raise ctypes.WinError(ERROR_NOT_ALL_ASSIGNED)
    finally:
        kernel32.CloseHandle(hToken)


def disable_privilege(privilege) -> None:
    hToken = wintypes.HANDLE()
    luid = LUID()
    tp = TOKEN_PRIVILEGES()
    advapi32.LookupPrivilegeValueW(None, privilege, ctypes.byref(luid))
    tp.Privileges[0].Luid = luid
    tp.Privileges[0].Attributes = 0
    advapi32.OpenProcessToken(kernel32.GetCurrentProcess(),
                              TOKEN_ALL_ACCESS,
                              ctypes.byref(hToken))
    try:
        advapi32.AdjustTokenPrivileges(hToken, False,
                                       ctypes.byref(tp),
                                       ctypes.sizeof(tp),
                                       None, None)
        if ctypes.get_last_error() == ERROR_NOT_ALL_ASSIGNED:
            raise ctypes.WinError(ERROR_NOT_ALL_ASSIGNED)
    finally:
        kernel32.CloseHandle(hToken)
