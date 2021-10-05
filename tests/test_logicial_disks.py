#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Windows NTFS & ReFS ownership/ACL tools

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "tests.windows_tools.logical_disks"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2021 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2021060201"

import subprocess

from windows_tools.logical_disks import (
    _get_logical_disks_plaintest,
    _get_logical_disks_win32api,
    _get_logical_disks_psutil,
    get_logical_disks,
)


def test__get_logical_disks_plaintest():
    result = _get_logical_disks_plaintest()
    print("Found disks via plaintest: ", result)
    assert isinstance(result, list), "get_logical_disks() should return list of str"
    assert "C:" in result, "We should at least have systemdrive C:"


def test__get_logical_disks_win32api():
    result = _get_logical_disks_win32api()
    print("Found disks via win32api: ", result)
    assert isinstance(result, list), "get_logical_disks() should return list of str"
    assert "C:" in result, "We should at least have systemdrive C:"


def test__get_logical_disks_psutil():
    result = _get_logical_disks_psutil()
    print("Found disks via psutil: ", result)
    assert isinstance(result, list), "get_logical_disks() should return list of str"
    assert "C:" in result, "We should at least have systemdrive C:"


def test_get_logical_disks():
    # Create a network
    command = r"net use Q: /DELETE"
    try:
        subprocess.check_output(command, shell=True, timeout=4)
    except subprocess.CalledProcessError:
        pass
    command = r"net use Q: \\localhost\c$\windows\temp"
    print(command)
    output = subprocess.check_output(command, shell=True, timeout=4)
    print("Creating network drive: ", output)
    no_net = get_logical_disks(include_network_drives=False)
    net_result = get_logical_disks(include_network_drives=True)
    # Delete the network drive
    command = "net use Q: /DELETE"
    output = subprocess.check_output(command, shell=True, timeout=4)
    print("Deleting network drive: ", output)
    print("Found disks from meta function without network drives: ", no_net)
    print("Found disks from meta function including network drives: ", net_result)

    assert len(no_net) < len(
        net_result
    ), "List without network drives should be smaller than list with network drives"
    assert isinstance(no_net, list), "get_logical_disks() should return list of str"
    assert "C:" in no_net, "We should at least have systemdrive C:"
    assert isinstance(net_result, list), "get_logical_disks() should return list of str"
    assert "C:" in net_result, "We should at least have systemdrive C:"


if __name__ == "__main__":
    print("Example code for %s, %s" % (__intname__, __build__))
    test__get_logical_disks_plaintest()
    test__get_logical_disks_win32api()
    test__get_logical_disks_psutil()
    test_get_logical_disks()
