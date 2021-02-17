#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
windows server identification

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'tests.windows_tools.server'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__build__ = '2021021601'

from windows_tools.server import *


def test_is_windows_server():
    """
    This test is very simple since we won't know for sure if actually running on server
    So we only test functionality here, actual tests have been done manually
    """
    is_server = is_windows_server()
    print('This machine is a windows server: ', is_server)
    assert is_server is True or is_server is False, 'is_server should be a boolean'


def test_is_rds_server():
    """
    This test is very simple since we won't know for sure if actually running on rds server
    So we only test functionality here, actual tests have been done manually
    """
    is_rds = is_rds_server()
    print('This machine is a windows RDS server: ', is_rds)
    assert is_rds is True or is_rds is False, 'is_rds should be a boolean'


if __name__ == '__main__':
    print('Example code for %s, %s' % (__intname__, __build__))
    test_is_windows_server()
    test_is_rds_server()
