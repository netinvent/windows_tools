#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
Retrieve bitlocker status and protector keys

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'windows_tools.bitlocker'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2018-2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.1.4'
__build__ = '2021021601'

from logging import getLogger
from typing import Union, List

from command_runner import command_runner

from windows_tools.logical_disks import get_logical_disks

logger = getLogger()


def get_bitlocker_drive_status(drive: str) -> Union[str, None]:
    """
    Returns a string that describes the current bitlocker status for a drive
    """
    exit_code, result = command_runner('where manage-bde', valid_exit_codes=[0, 1])
    if exit_code != 0:
        logger.debug('Bitlocker management tool not installed.')
        return None
    exit_code, result = command_runner('manage-bde {} -status'.format(drive), encoding='cp437')
    if exit_code == 0:
        return result
    # -2147217405 (cmd) or 2147749891 (Python) == (0x80041003) = Permission denied
    if exit_code in [-2147217405, 2147749891]:
        logger.warning('Don\'t have permission to get bitlocker drive status for {}.'.format(drive))
    else:
        logger.warning('Cannot get bitlocker drive status for {}.'.format(drive))
        logger.warning('{}'.format(result))
    return None


def get_bitlocker_protection_key(drive: str) -> Union[str, None]:
    """
    Returns a string containing the protection key of a bitlocked drive
    """
    exit_code, result = command_runner('where manage-bde', valid_exit_codes=[0, 1])
    if exit_code != 0:
        logger.debug('Bitlocker management tool not installed.')
        return None
    # utf-8 produces less good results on latin alphabets, but better results on logographic / syllabic alphabets
    exit_code, result = command_runner('manage-bde -protectors {} -get'.format(drive), encoding='utf-8')
    if exit_code == 0:
        return result
    # -2147217405 (cmd) or 2147749891 (Python) == (0x80041003) = Permission denied
    if exit_code in [-2147217405, 2147749891]:
        logger.warning('Don\'t have permission to get bitlocker drive protectors for {}.'.format(drive))
    # -1 is returned in cmd on valid drive without protectors (or as unsigned 2^32-1 = 4294967295 in Python)
    elif exit_code in [-1, 4294967295]:
        logger.debug('Drive {} does not seem to have bitlocker protectors yet.'.format(drive))
    # -2147024809 is returned on invalid drives (eg network drives, inexisting drives)
    else:
        logger.warning('Could not get bitlocker protector for drive {}: {}'.format(drive, result))
    return None


def get_bitlocker_status() -> List[str]:
    """
    Return bitlocker status for all drives
    """
    bitlocker_status = {}
    # Only NTFS / ReFS drives are allowed to have bitlocker
    for drive in get_logical_disks(include_non_ntfs_refs=False, include_network_drives=False):
        bitlocker_status[drive] = get_bitlocker_drive_status(drive)
    return bitlocker_status

def get_bitlocker_keys() -> List[str]:
    """
    Return bitlocker protection keys for all drives
    """
    bitlocker_keys = {}
    for drive in get_logical_disks(include_non_ntfs_refs=False, include_network_drives=False):
        if get_bitlocker_drive_status(drive):
            bitlocker_keys[drive] = get_bitlocker_protection_key(drive)
    return bitlocker_keys


def get_bitlocker_full_status() -> dict:
    """
    Return full bitlocker status for all drives
    """
    bitlocker_full_status = {}
    for drive in get_logical_disks(include_non_ntfs_refs=False, include_network_drives=False):
        bitlocker_full_status[drive] = {'status': get_bitlocker_drive_status(drive),
                                        'protectors': get_bitlocker_protection_key(drive)
                                        }
    return bitlocker_full_status
