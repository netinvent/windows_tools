#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Tool to run as another user

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "tests.windows_tools.impersonate"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2021 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2021021601"

import subprocess
from random import random

import win32api

from windows_tools.impersonate import *


def test_ImpersonateWin32Sec():
    # create a test user
    TEST_USERNAME = "test_user_{}".format(int(random() * 100000))
    TEST_PASSWORD = "test_pw_{}".format(int(random() * 100000))

    command = "net user {} {} /ADD".format(TEST_USERNAME, TEST_PASSWORD)
    print(command)
    output = subprocess.check_output(command, shell=True, timeout=4)
    print("Creating test user: ", output)

    current_user = win32api.GetUserName()
    print("Current  user: ", current_user)
    with ImpersonateWin32Sec(
        domain=".", username=TEST_USERNAME, password=TEST_PASSWORD
    ):
        imp_current_user = win32api.GetUserName()
        print("Current impersonated user: ", current_user)
        assert (
            current_user != imp_current_user
        ), "Current user and test user should be different"
        assert (
            imp_current_user == TEST_USERNAME
        ), "Impersonated user should be test user"

    command = "net user {} /DELETE".format(TEST_USERNAME)
    output = subprocess.check_output(command, shell=True, timeout=4)
    print("Removing test user: ", output)
    current_user = win32api.GetUserName()
    print("Current  user: ", current_user)

    assert (
        current_user != imp_current_user
    ), "Current user and test user should be different now"


if __name__ == "__main__":
    print("Example code for %s, %s" % (__intname__, __build__))
    test_ImpersonateWin32Sec()
