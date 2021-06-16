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

__intname__ = 'windows_tools.product_key'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__description__ = 'Retrieve Windows Product Keys'
__licence__ = 'BSD 3 Clause'
__version__ = '0.3.2'
__build__ = '2021061601'

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
            rpk[j + rpkOffset] = int(dwAccumulator / 24) if int(dwAccumulator / 24) <= 255 else 255
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
        return decode_key(windows_tools.registry.get_value(hive=windows_tools.registry.HKEY_LOCAL_MACHINE,
                                                           key=r'SOFTWARE\Microsoft\Windows NT\CurrentVersion',
                                                           value='DigitalProductID',
                                                           arch=windows_tools.registry.KEY_WOW64_32KEY | windows_tools.registry.KEY_WOW64_64KEY))
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

    product_key = windows_tools.wmi_queries.query_wmi('SELECT OA3xOriginalProductKey FROM SoftwareLicensingService')
    try:
        return product_key[0]['OA3xOriginalProductKey']
    except (TypeError, IndexError, KeyError, AttributeError):
        return None
