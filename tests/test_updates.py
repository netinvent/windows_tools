#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Get updates installed by Windows Update, including those the QFE doesn't list

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'tests.windows_tools.updates'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2021 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__build__ = '2021092101'


from windows_tools.updates import *

def test_get_all_windows_updates():
    updates = get_windows_updates()

    assert isinstance(updates, list), 'Result should be a list'

    for update in updates:
        print(update)


def test_get_windows_updates_filtered():
    updates = get_windows_updates(filter_multiple=True)

    assert isinstance(updates, list), 'Result should be a list'

    already_seen = []
    for update in updates:
        if update['title'] not in already_seen:
            already_seen.append(update['title'])
        else:
            assert False, 'We have a title double'
        print(update)



if __name__ == '__main__':
    print('Example code for %s, %s' % (__intname__, __build__))
    test_get_all_windows_updates()
    test_get_windows_updates_filtered()