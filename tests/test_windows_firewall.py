#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Simple registry check for windows firewall status

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "tests.windows_tools.windows_firewall"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2021 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2021021601"

from windows_tools.windows_firewall import *


def test_is_firewall_active():
    """
    Too simple check here, has been tested manually
    We won't know for sure in advance if firewall should be enabled
    """
    result = is_firewall_active()
    print("Windows firewall status: ", result)
    assert result is True or result is False, "Result should be a boolean"


if __name__ == "__main__":
    print("Example code for %s, %s" % (__intname__, __build__))
    test_is_firewall_active()
