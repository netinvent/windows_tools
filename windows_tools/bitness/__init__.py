#! /usr/bin/env python
#  -*- coding: utf-8 -*-

# This file is part of windows_tools module

"""
Basic way to determine if windows platform is 64 bit

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "windows_tools.bitness"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2016-2023 Orsiris de Jong"
__description__ = "bitness identification for Windows based on environment"
__licence__ = "BSD 3 Clause"
__version__ = "0.2.0"
__build__ = "2023112701"


import os

# python 2.7 compat fixes
try:
    from typing import Optional
except ImportError:
    pass
try:
    import win32file

    _HAS_WIN32FILE = True
except ImportError:
    _HAS_WIN32FILE = False
    print("Cannot import win32file. Bitness autodetction won't work")


def is_64bit():
    # type: () -> bool
    """
    Detect windows bitness
    # https: // stackoverflow.com / a / 12578715 improved

    """
    # This environment variable exists on 32bit cmd.exe executed on 64 bit arch
    if "PROCESSOR_ARCHITEW6432" in os.environ:
        return True
    # Possible values of PROCESSOR_ARCHITECURE is AMD64, IA64, ARM64 and EM64T(Rare, only on Windows XP 64)
    if "PROCESSOR_ARCHITECTURE" in os.environ:
        return os.environ["PROCESSOR_ARCHITECTURE"].endswith("64") or os.environ[
            "PROCESSOR_ARCHITECTURE"
        ].endswith("64T")
    return "PROGRAMFILES(X86)" in os.environ


def is_64bit_executable(filename):
    # type: (str) -> Optional[bool]
    if _HAS_WIN32FILE:
        return win32file.GetBinaryType(filename) == 6
    else:
        return None
