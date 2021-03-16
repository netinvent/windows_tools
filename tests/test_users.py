#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Simple check if Windows is 64 bit

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'tests.windows_tools.users'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__build__ = '2021031601'

from windows_tools.users import *


def test_well_known_sids():
    admins_group_sid = well_known_sids(username='Administrators')
    assert admins_group_sid == 'S-1-5-32-544', 'well_known_sids(username="Administrators") ' \
                                               'should return SID "S-1-5-32-544"'

    admins_group_name = well_known_sids(sid='S-1-5-32-544')
    assert admins_group_name == 'Administrators', 'well_known_sids(sid="S-1-5-32-544") should return "Administrators"'


def test_whoami():
    current_user = whoami()
    assert isinstance(current_user, str), 'Current username should be a string'


def test_get_username_from_sid():
    builtin_admin = get_username_from_sid('S-1-5-32-544')
    print('Builtin Admins: ', builtin_admin)
    assert builtin_admin[0][0:5] == 'Admin', r'BUILINT\Administrators group name should begin with "Admin".' \
                                             'Careful, this is not always valid depending on the system locale'
    assert builtin_admin[1] == 'BUILTIN', r'BUILTIN\Administrators domain should be BUILTIN'
    assert builtin_admin[2] == 4, r'BUILTIN\Administrators type shoud be 4'

    system_account = get_username_from_sid('S-1-5-18')
    print('System account: ', system_account)
    assert system_account[0][0:3].upper() == 'SYS', 'System account name should begin with Sys.' \
                                            ' Careful, this is not always valid dpeending on the system locale'
    # Again, we make the assumption that all locale system account domains will contain 'NT' and 'AUT'
    # but not 'AUTH' (eg french 'AUTORITE NT')
    assert 'AUT' in system_account[1] and 'NT' in system_account[1], 'System account domain should be NT ' \
                                                                     'AUTHORITY or something alike depending ' \
                                                                     'on system locale'
    assert system_account[2] == 5, 'System account type should be 5'


def test_get_pysid():
    current_user = get_pysid()
    # We cannot check if current_user is a PySID class object since we don't have the definition of that class
    # Let's fallback to some basic test anyway
    assert current_user.__class__.__name__ == 'PySID', 'Returned object should be a PySID'
    assert 'PySID:S-1-5-21-' in current_user.__str__(), 'Current user does not seem to be a valid PySID object'
    print('Current User SID: {}'.format(current_user))
    system_account = get_pysid('S-1-5-18')
    print('System Account SID: {}'.format(system_account))
    assert system_account.__class__.__name__ == 'PySID', 'Returned object should be a PySID'
    assert 'PySID:S-1-5-18' == system_account.__str__(), 'System account PySID does not seem valid'

    admins_group_by_sid = get_pysid('S-1-5-32-544')
    admins_group_name, _, _ = get_username_from_sid('S-1-5-32-544')
    admins_group_by_name = get_pysid(admins_group_name)
    assert admins_group_by_sid.__class__.__name__ == 'PySID', 'Returned object should be a PySID'
    assert admins_group_by_name == admins_group_by_sid, 'Both admin group lookups should be equal'


def test_get_pysid_from_username():
    admins_group_name, _, _ = get_username_from_sid('S-1-5-32-544')
    admins_group_sid = get_pysid_from_username(admins_group_name)
    print('Admin group: ', admins_group_sid)
    assert admins_group_sid[0].__class__.__name__ == 'PySID', 'Returned object should be a PySID'
    assert 'PySID:S-1-5-32-544' in admins_group_sid[
        0].__str__(), 'get_binary_user_info should return a PySID as first element of the returned tuple'


if __name__ == '__main__':
    print('Example code for %s, %s' % (__intname__, __build__))
    test_well_known_sids()
    test_whoami()
    test_get_username_from_sid()
    test_get_pysid()
    test_get_pysid_from_username()
