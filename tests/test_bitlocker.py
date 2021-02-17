#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Retrieve bitlocker status and protector keys

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'tests.windows_tools.bitlocker'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__build__ = '2021021501'

from windows_tools.bitlocker import *


def test_get_bitlocker_full_status():
    """
    There's no real test I can write for bitlocker unless the target machine has a bitlocker enabled drive
    So here we are writing basic tests
    """
    result = get_bitlocker_full_status()
    assert result['C:']['status'] is not False, 'C: bitlocker status must be None or a string'
    assert result['C:']['protectors'] is not False, 'C: protectors should be None or a string'


if __name__ == '__main__':
    print('Example code for %s, %s' % (__intname__, __build__))
    test_get_bitlocker_full_status()
