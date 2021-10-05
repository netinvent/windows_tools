#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Microsoft Powershell runner class

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "tests.windows_tools.powershell"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2021 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2021021601"

from windows_tools.powershell import *


def test_PowerShellRunner():
    """ """

    P = PowerShellRunner()
    interpreter = P.powershell_interpreter
    print("Powershell interpreter: ", interpreter)
    assert interpreter is not None, "Powershell interpreter not found"
    version = P.get_version()
    print("Powershell version: ", version)
    assert isinstance(
        version, tuple
    ), "Powerhsell version should be a tuple of two ints"
    assert 0 < int(version[0]) < 10, "Powershell "

    exit_code, output = P.run_command("Get-ComputerInfo | Select OsInstallDate")
    assert exit_code == 0, "Command exit code should be zero"
    print(output)


if __name__ == "__main__":
    print("Example code for %s, %s" % (__intname__, __build__))
    test_PowerShellRunner()
