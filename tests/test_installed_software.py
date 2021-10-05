#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
List of installed software from Uninstall registry keys, 32 and 64 bits

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "tests.windows_tools.installed_software"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2021 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2021021601"

import subprocess
from random import random

from windows_tools.installed_software import *


def test_get_installed_software():
    # Add temporary software entries
    fake_software_name = "MyTestSoftwareregEntry{}".format(int(random() * 100000))
    command = (
        r"reg add HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\Test_windows_tools.installed_software"
        r" /v DisplayName /t REG_SZ /d {} /f".format(fake_software_name)
    )
    print(command)
    output = subprocess.check_output(command, shell=True, timeout=4)
    print("Creating fake software entry: ", output)
    print("Listing installed software")
    result = get_installed_software()
    assert isinstance(result, list)
    assert isinstance(
        result[0], dict
    ), "get_installed_software() should return list of dict"
    fake_software_present = False
    for entry in result:
        print(entry)
        if entry["name"] == fake_software_name:
            fake_software_present = True

    command = (
        r"reg delete"
        r" HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\Test_windows_tools.installed_software /f"
    )
    output = subprocess.check_output(command, shell=True, timeout=4)
    print("Deleting fake software entry: ", output)
    print("Fake software entry present: ", fake_software_present)
    assert fake_software_present, "Fake software entry is not present"


if __name__ == "__main__":
    test_get_installed_software()
