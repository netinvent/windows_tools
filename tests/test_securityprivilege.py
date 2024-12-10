#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Privilege enabling / disabling

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "tests.windows_tools.securityprivilege"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2024 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2021021601"

from windows_tools.securityprivilege import *


def test_enable_privilege():
    print("Enabling SeSecurityPrivilege")
    enable_privilege("SeSecurityPrivilege")


def test_disable_privilege():
    print("Disabling SeSecurityPrivilege")
    disable_privilege("SeSecurityPrivilege")


if __name__ == "__main__":
    print("Example code for %s, %s" % (__intname__, __build__))
    test_enable_privilege()
    test_disable_privilege()
