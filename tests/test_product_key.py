#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Find Windows Product key from registry and various

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'tests.windows_tools.product_key'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__build__ = '2021021601'

import re

from windows_tools.product_key import *

PRODUCT_KEY_REGEX = r'([A-Z0-9]{5}-){4}[A-Z0-9]{5}'


def test_get_windows_product_key_from_wmi():
    wmi_key = get_windows_product_key_from_wmi()
    print('Key from WMI: %s' % wmi_key)
    assert re.match(PRODUCT_KEY_REGEX, wmi_key), 'Found product key matches product key format'


def test_get_windows_product_key_from_reg():
    reg_key = get_windows_product_key_from_reg()
    print('Key from REG: %s' % reg_key)
    assert re.match(PRODUCT_KEY_REGEX, reg_key), 'Found product key matches product key format'


if __name__ == '__main__':
    print('Example code for %s, %s' % (__intname__, __build__))
    test_get_windows_product_key_from_wmi()
    test_get_windows_product_key_from_reg()
