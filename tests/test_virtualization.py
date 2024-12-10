#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
virtualization identification

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "tests.windows_tools.virtualization"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2024 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2021021601"

from windows_tools.virtualization import *


def test_get_relevant_platform_info():
    platform_info = get_relevant_platform_info()
    print(platform_info)
    assert isinstance(platform_info, dict), "platform info should ba a dictionnary"
    assert isinstance(
        next(iter(platform_info.values())), dict
    ), "Virtualization check is not a sub-dictionnary"
    assert isinstance(
        platform_info["computersystem"]["Manufacturer"], str
    ), "computer manufacturer should be found"
    assert isinstance(
        platform_info["baseboard"]["Manufacturer"], str
    ), "baseboard manufacturer should be found"
    assert isinstance(
        platform_info["bios"]["Manufacturer"], str
    ), "bios manufacturer should be found"
    assert isinstance(
        platform_info["diskdrive"]["DeviceID"], str
    ), "computer should at least have one physical disk"


def test_check_for_virtualization():
    """
    Simple checks since we won't know for sure what platform we run on
    """
    is_virtual, hypervisor = check_for_virtualization(get_relevant_platform_info())
    print("Virt check: ", is_virtual, hypervisor)
    assert is_virtual is True or is_virtual is False, "virt check should be a boolean"
    assert isinstance(hypervisor, str), "virt variant should be a string"


if __name__ == "__main__":
    print("Example code for %s, %s" % (__intname__, __build__))
    test_get_relevant_platform_info()
    test_check_for_virtualization()
