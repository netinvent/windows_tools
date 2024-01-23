#! /usr/bin/env python
#  -*- coding: utf-8 -*-

# This file is part of windows_tools module

"""
Find Windows Product key from registry and various

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "windows_tools.product_key"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2024 Orsiris de Jong"
__description__ = "Retrieve Windows Product Keys"
__licence__ = "BSD 3 Clause"
__version__ = "0.4.0"
__build__ = "2024012301"

from typing import Optional

import windows_tools.registry
import windows_tools.wmi_queries


def decode_key(rpk: str) -> str:
    """
    Decodes a product key from registry (worked with XP, fails with newer Windows versions)

    This function is derived from https://gist.github.com/Spaceghost/877110

    :param rpk: (str) encoded product key
    :return: (str) product key in XXXXX-XXXXX-XXXXX-XXXXX-XXXXX format
    """
    rpkOffset = 52
    i = 28
    szPossibleChars = "BCDFGHJKMPQRTVWXY2346789"
    szProductKey = ""

    # Convert rpk to list so we can iter
    rpk = list(rpk)

    while i >= 0:
        dwAccumulator = 0
        j = 14
        while j >= 0:
            dwAccumulator = dwAccumulator * 256
            d = rpk[j + rpkOffset]
            if isinstance(d, str):
                d = ord(d)
            dwAccumulator = d + dwAccumulator
            rpk[j + rpkOffset] = (
                int(dwAccumulator / 24) if int(dwAccumulator / 24) <= 255 else 255
            )
            dwAccumulator = dwAccumulator % 24
            j = j - 1
        i = i - 1
        szProductKey = szPossibleChars[dwAccumulator] + szProductKey

        if ((29 - i) % 6) == 0 and i != -1:
            i = i - 1
            szProductKey = "-" + szProductKey
    return szProductKey


def get_windows_product_key_from_reg() -> Optional[str]:
    """
    Searched registry for product key
    :return: (str) product key
    """
    try:
        return decode_key(
            windows_tools.registry.get_value(
                hive=windows_tools.registry.HKEY_LOCAL_MACHINE,
                key=r"SOFTWARE\Microsoft\Windows NT\CurrentVersion",
                value="DigitalProductID",
                arch=windows_tools.registry.KEY_WOW64_32KEY
                | windows_tools.registry.KEY_WOW64_64KEY,
            )
        )
    except FileNotFoundError:
        # regisrty key not found
        pass
    except Exception:
        # decoder error can be anything
        pass
    return None


def get_windows_product_key_from_wmi() -> Optional[str]:
    """
    Searches WMI for productkey
    """

    product_key = windows_tools.wmi_queries.query_wmi(
        "SELECT OA3xOriginalProductKey FROM SoftwareLicensingService",
        name="windows_tools.product_key.get_windows_product_key_from_wmi",
    )
    try:
        return product_key[0]["OA3xOriginalProductKey"]
    except (TypeError, IndexError, KeyError, AttributeError):
        return None


def get_windows_product_channel() -> Optional[str]:
    """
    Tries to get Windows license type (OEM/Retail/Volume)

    So basically there's no good way to get that info, but the description field in SoftwareLicenseingProduct 
    should have OEM/Volume/Retail in string
    Tested on Win10/11. Please test and report on other Windows versions

    Quick and dirty python implementation of 
    https://stackoverflow.com/questions/56754546/powershell-windows-license-type#comment100070333_56754958
    """
    license_description = windows_tools.wmi_queries.query_wmi(
        'SELECT Description FROM SoftwareLicensingProduct WHERE Description LIKE "Windows%" AND LicenseStatus = 1'
    )

    if isinstance(license_description, list):
        try:
            ld = license_description[0]["Description"].upper()
            if "VOLUME_MAK" in ld:
                return "VOLUME_MAK"
            elif "OEM_SLP" in ld:
                return "OEM_SLP"
            elif "RETAIL" in ld:
                return "RETAIL"
            elif "OEM_COA_NSLP" in ld:
                return "OEM_COA_NSLP"
            elif "OEM_COA_SLP" in ld:
                return "OEM_COA_SLP"
            # Fuzzy detection from here
            elif "VOLUME" in ld:
                return "VOLUME"
            elif "OEM" in ld:
                return "OEM"
        except (KeyError, IndexError, TypeError, AttributeError):
            pass
        return "UNKNOWN"
