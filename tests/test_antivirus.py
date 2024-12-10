#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
antivirus functions help to obtain Windows security antivirus state

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "tests.windows_tools.antivirus"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2024 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2021020901"

from windows_tools.antivirus import (
    securitycenter_get_product_type,
    securitycenter_get_product_update_state,
    securitycenter_get_product_exec_state,
    get_installed_antivirus_software,
)


# Those states are obtained via WMI securitycenter2/antivirusproduct & securitycenter2/firewallproduct
AV_DISABLED_AND_UP_TO_DATE = 262144
AV_ENABLED_AND_UP_TO_DATE = 266240
FW_ENABLED = 69632
FW_DISABLED = 65536
AV_BOGUS_STATE = 307302933
AV_DEFENDER_DISABLED_AND_UP_TO_DATE = 393472
AV_DEFENDER_ENABLED_AND_OUT_OF_DATE = 397584
AV_DEFENDER_ENABLED_AND_UP_TO_DATE = 397568


def test_securitycenter_get_product_type():
    assert (
        securitycenter_get_product_type(AV_DISABLED_AND_UP_TO_DATE) == "Antivirus"
    ), "Product type should be antivirus"
    assert (
        securitycenter_get_product_type(AV_ENABLED_AND_UP_TO_DATE) == "Antivirus"
    ), "Product type should be antivirus"
    assert (
        securitycenter_get_product_type(FW_ENABLED) == "Firewall"
    ), "Product type should be firewall"
    assert (
        securitycenter_get_product_type(FW_DISABLED) == "Firewall"
    ), "Product type should be firewall"
    try:
        securitycenter_get_product_type(AV_BOGUS_STATE)
    except ValueError:
        pass
    else:
        assert False, "Bogus AV state should trigger an error"


def test_securitycenter_get_product_exec_state():
    assert (
        securitycenter_get_product_exec_state(AV_DISABLED_AND_UP_TO_DATE) is False
    ), "Product state should be disabled"
    assert (
        securitycenter_get_product_exec_state(AV_ENABLED_AND_UP_TO_DATE) is True
    ), "Product state should be enabled"
    assert (
        securitycenter_get_product_exec_state(FW_ENABLED) is True
    ), "Product state should be enabled"
    assert (
        securitycenter_get_product_exec_state(FW_DISABLED) is False
    ), "Product state should be disabled"


def test_securitycenter_get_product_update_state():
    assert (
        securitycenter_get_product_update_state(AV_DISABLED_AND_UP_TO_DATE) is True
    ), "Product state should be uptodate"
    assert (
        securitycenter_get_product_update_state(AV_ENABLED_AND_UP_TO_DATE) is True
    ), "Product state should be uptodate"


def test_get_installed_antivirus_software():
    result = get_installed_antivirus_software()
    print("Antivirus software:\n")
    print(result)
    assert isinstance(result, list) is True, "AV product list should be a list"
    if result != []:
        assert isinstance(result[0]["name"], str) is True, (
            "First found AV product name should be a string."
            "Please execute this test on a Windows machine with an AV engine installed,"
            " otherwise disable this test. PS: Windows defender does not count as AV engine"
        )


if __name__ == "__main__":
    print("Example code for %s, %s" % (__intname__, __build__))
    test_securitycenter_get_product_type()
    test_securitycenter_get_product_exec_state()
    test_securitycenter_get_product_update_state()
    test_get_installed_antivirus_software()
