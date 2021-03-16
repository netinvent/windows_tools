#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
Microsoft Office identification

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'windows_tools.office'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong'
__description__ = 'Microsoft Office identification, works for click and run, o365 and elder versions'
__licence__ = 'BSD 3 Clause'
__version__ = '0.1.1'
__build__ = '2021031601'

from typing import Tuple, Optional

from windows_tools import registry

# Let's make sure the dictionnary goes from most recent to oldest
KNOWN_VERSIONS = {
    '16.0': '2016/2019/O365',
    '15.0': '2013',
    '14.0': '2010',
    '12.0': '2007',
    '11.0': '2003',
    '10.0': '2002',
    '9.0': '2000',
    '8.0': '97',
    '7.0': '95',
}


def _get_office_click_and_run_ident():
    # type: () -> Optional[str]
    """
    Get ClickAndRun Product Id for Office 2016/2019/O365 detection
    Example of result "ProPlus2019Volume,VisioPro2019Volume"
    """
    try:
        click_and_run_ident = registry.get_value(registry.HKEY_LOCAL_MACHINE,
                                                 r'Software\Microsoft\Office\ClickToRun\Configuration',
                                                 'ProductReleaseIds',
                                                 arch=registry.KEY_WOW64_64KEY | registry.KEY_WOW64_32KEY, )
    except FileNotFoundError:
        click_and_run_ident = None
    return click_and_run_ident


def _get_used_word_version():
    # type: () -> Optional[int]
    """
    Try do determine which version of Word is used (in case multiple versions are installed)
    """
    try:
        word_ver = registry.get_value(registry.HKEY_CLASSES_ROOT, r'Word.Application\CurVer', None)
    except FileNotFoundError:
        word_ver = None
    try:
        version = int(word_ver.split('.')[2])
    except (IndexError, ValueError, AttributeError):
        version = None
    return version


def _get_installed_office_version():
    # type: () -> Optional[str, bool]
    """
    Try do determine which is the highest current version of Office installed
    """
    for possible_version, _ in KNOWN_VERSIONS.items():
        try:
            office_keys = registry.get_keys(registry.HKEY_LOCAL_MACHINE,
                                            r'SOFTWARE\Microsoft\Office\{}'.format(possible_version),
                                            recursion_level=2,
                                            arch=registry.KEY_WOW64_64KEY | registry.KEY_WOW64_32KEY,
                                            combine=True)

            try:
                is_click_and_run = True if office_keys['ClickToRunStore'] is not None else False
            except (TypeError, KeyError):
                is_click_and_run = False

            try:
                # Let's say word is the reference (since we could also have powerpoint viewer or so)
                is_valid = True if office_keys['Word'] is not None else False
                if is_valid:
                    return possible_version, is_click_and_run
            except KeyError:
                pass
        except FileNotFoundError:
            pass
    return None, None


def get_office_version():
    # type: () -> Tuple[str, Optional[str]]
    """
    It's plain horrible to get the office version installed
    Let's use some tricks, ie detect current Word used
    """

    word_version = _get_used_word_version()
    office_version, is_click_and_run = _get_installed_office_version()

    # Prefer to get used word version instead of installed one
    if word_version is not None:
        office_version = word_version

    if office_version is not None:
        version = float(office_version)
    else:
        version = None
    click_and_run_ident = _get_office_click_and_run_ident()

    def _get_office_version():
        # type: () -> str
        if version is not None:
            if version < 16:
                try:
                    return KNOWN_VERSIONS['{}.0'.format(version)]
                except KeyError:
                    pass
            # Special hack to determine which of 2016, 2019 or O365 it is
            if version == 16:
                if isinstance(click_and_run_ident, str):
                    if '2016' in click_and_run_ident:
                        return '2016'
                    if '2019' in click_and_run_ident:
                        return '2019'
                    if 'O365' in click_and_run_ident:
                        return 'O365'
                return '2016/2019/O365'
            # Let's return whatever we found out
            return 'Unknown: {}'.format(version)
        return None

    if isinstance(click_and_run_ident, str) or is_click_and_run:
        click_and_run_suffix = 'ClickAndRun'
    else:
        click_and_run_suffix = None

    return _get_office_version(), click_and_run_suffix
