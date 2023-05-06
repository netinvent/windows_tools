#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Simple check if Windows is 64 bit

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "tests.windows_tools.bitness"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2023 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2021050601"

from windows_tools.bitness import *


def test_is_64bit():
    """
    Again, we can only assume that all tests are done on 64 bit systems nowadays
    """
    assert is_64bit() is True, "tests should probably be run on a 64 bit system"
    print("Is this a bit system ?", is_64bit())


if __name__ == "__main__":
    print("Example code for %s, %s" % (__intname__, __build__))
    test_is_64bit()
