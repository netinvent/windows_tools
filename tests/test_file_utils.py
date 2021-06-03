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

__intname__ = 'tests.windows_tools.file_utils'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__build__ = '2021021501'

import os
import shutil
from random import random

from windows_tools.file_utils import *
from windows_tools.users import *

TEST_DIR = os.path.join(os.environ.get('TEMP', r'C:\Windows\Temp'), __file__ +
                        'TestDir{}'.format(int(random() * 100000)))
TEST_FILE = os.path.join(os.environ.get('TEMP', r'C:\Windows\Temp'), os.path.basename(__file__) +
                         '.Test{}'.format(int(random() * 100000)))


def test_get_ownership():
    """
    Again, we can only assume that all tests are done on 64 bit systems nowadays
    """
    local_windows_dir = r'C:\Windows'

    owner = get_ownership(local_windows_dir)
    print('{} directory owner; {}.'.format(local_windows_dir, owner))
    assert owner[0] == 'TrustedInstaller', '{}} file owner bogus, should be TrustedInstaller since win7'.format(
        local_windows_dir)
    assert owner[1] == 'NT SERVICE', '{} file owner should be of group NT SERVICE since Win7'.format(local_windows_dir)
    assert owner[2] == 5, '{} file owner rights should be 5 since Win7'.format(local_windows_dir)


def test_take_ownership():
    """
    Let's create a file, check it's owner, than change it and test again
    """
    if os.path.isfile(TEST_FILE):
        os.remove(TEST_FILE)
    with open(TEST_FILE, 'w') as file_handle:
        file_handle.write('SOME TEXT')

    owner = get_ownership(TEST_FILE)
    print('Current file owner: ', TEST_FILE, owner)

    # In order to use set_file_owner, we need a PySID object as owner
    system_account = get_pysid(well_known_sids(username='System'))
    result = take_ownership(TEST_FILE, owner=system_account, force=True)

    new_owner = get_ownership(TEST_FILE)
    print('Current file owner: ', TEST_FILE, new_owner)
    new_owner_sid = get_pysid_from_username(new_owner[0])
    assert result is True, 'take_ownership result is not true: "{}"'.format(result)
    assert new_owner_sid[0].__str__() == 'PySID:S-1-5-18', 'File should now be owned by system account'
    assert new_owner != owner, 'Earlier owner and current owner should differ unless tests are run as system'

    if os.path.isfile(TEST_FILE):
        os.remove(TEST_FILE)


def test_take_ownership_recursive():
    if os.path.isdir(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)

    print('Test take_ownership_recursive()')
    owner = get_pysid(well_known_sids(username='Everyone'))
    take_ownership_recursive(TEST_DIR, owner=owner)

    shutil.rmtree(TEST_DIR)


def test_easy_permissions():
    easy_perm = easy_permissions('R')
    assert easy_perm == -2147483648, 'Permission bitmask wrong for R'
    easy_perm = easy_permissions('RX')
    assert easy_perm == -1610612736, 'Permission bitmask wrong for RX'
    easy_perm = easy_permissions('RWX')
    assert easy_perm == -536870912, 'Permission bitmask wrong for RWX'
    easy_perm = easy_permissions('M')
    assert easy_perm == -536870912, 'Permission bitmask wrong for M'
    easy_perm = easy_permissions('F')
    assert easy_perm == 268435456, 'Permission bitmask wrong for F'
    try:
        easy_perm = easy_permissions('')
    except ValueError:
        assert easy_perm != 307302933, 'Bogus permission should have happened'


def test_set_acls():
    """
    Really basic test, TODO: improve with inheritance tests
    """
    if os.path.isfile(TEST_FILE):
        os.remove(TEST_FILE)
    with open(TEST_FILE, 'w') as file_handle:
        file_handle.write('SOME TEXT')

    print('Test setting ACLs')
    try:
        set_acls(TEST_FILE, user_list=[whoami()], owner=whoami(), permissions=easy_permissions('F'))
    except Exception as e:
        assert False, 'set_acls should not create an exception: {}'.format(e)

    os.remove(TEST_FILE)


def test_get_paths_recursive_and_fix_permissions():
    """
    Really basic tests too
    """
    print('Test get_files_recursive_and_fix_permissions')

    if os.path.isdir(TEST_DIR):
        get_paths_recursive_and_fix_permissions(TEST_DIR, owner=whoami(), permissions=easy_permissions('RWX'))
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)
    with open(os.path.join(TEST_DIR, os.path.basename(__file__) + '.tst'), 'w') as file_handle:
        file_handle.write('SOMETEXT')

    try:
        set_acls(TEST_DIR, user_list=[whoami()], owner=whoami(), permissions=easy_permissions('R'),
                 inherit=False, inheritance=False)
    except Exception as e:
        assert False, 'set_acls had an exception: {}'.format(e)

    # Normally, we should not be able to delete the fil since we set permissions as RX only
    try:
        # shutil.rmtree(TEST_DIR)
        pass
    except PermissionError as e:
        print('We have a permission error: '.format(e))
    else:
        pass
        # assert False, 'We should have a permission error here'

    try:
        get_paths_recursive_and_fix_permissions(TEST_DIR, permissions=easy_permissions('F'))
    except Exception as e:
        assert False, 'get_file_recursive_and_fix_permissions had an exception: {}'.format(e)

    try:
        shutil.rmtree(TEST_DIR)
    except PermissionError:
        assert False, 'This time, we should not have a permission error here'


if __name__ == '__main__':
    print('Example code for %s, %s' % (__intname__, __build__))
    test_get_ownership()
    test_take_ownership()
    test_take_ownership_recursive()
    test_easy_permissions()
    test_set_acls()
    # test_get_files_recursive_and_fix_permissions()  # TODO: fix set_acls(inherit=False) to not copy DACLs in order
    # to write this test correctly
