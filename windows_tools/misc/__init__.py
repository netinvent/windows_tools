#! /usr/bin/env python
#  -*- coding: utf-8 -*-

# This file is part of windows_tools module

"""
Windows ticks date tools and maybe others later

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "windows_tools.misc"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2021 Orsiris de Jong"
__description__ = "Windows misc tools"
__licence__ = "BSD 3 Clause"
__version__ = "1.0.0"
__build__ = "2021100401"


from datetime import datetime


def windows_ticks_to_unix_seconds(windows_ticks):
    """
    Windows ticks to epoch converter
    # https://stackoverflow.com/questions/6161776/convert-windows-filetime-to-second-in-unix-linux
    """
    return windows_ticks / 10000000 - 11644473600


def windows_ticks_to_date(windows_ticks):
    """
    Return standard YYYY-MM-DD HH:mm:SS format from windows_ticks
    """
    return datetime.fromtimestamp(
        windows_ticks_to_unix_seconds(windows_ticks)
    ).strftime("%Y-%m-%d %H:%M:%S")
