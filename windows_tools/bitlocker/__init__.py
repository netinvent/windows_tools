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
__description__ = 'Retrieve bitlocker status and protector keys for all drives'
__licence__ = 'BSD 3 Clause'
__version__ = '1.0.0'
__build__ = '2021060201'

from logging import getLogger
from typing import Union

from command_runner import command_runner

from windows_tools.logical_disks import get_logical_disks

logger = getLogger()

# Which filesystems may be bitlocker encrypted
BITLOCKER_ELIGIBLE_FS = ['NTFS', 'ReFS']


# Unless volume is unlocked, we won't know which filesystem is contained by a bitlocked drive


def check_bitlocker_management_tools() -> bool:
    """
    Checks whether bitlocker management tools are insqtalled
    """
    exit_code, result = command_runner('where manage-bde', valid_exit_codes=[0, 1, 4294967295])
    if exit_code != 0:
        logger.debug('Bitlocker management tools not installed. This might also happen when 32 bit Python '
                     'is run on 64 bit Windows.')
        logger.debug(result)
        return False
    return True


def get_bitlocker_drive_status(drive: str) -> Union[str, None]:
    """
    Returns a string that describes the current bitlocker status for a drive
    """
    if not check_bitlocker_management_tools():
        return None
    exit_code, result = command_runner('manage-bde {} -status'.format(drive), encoding='cp437')
    if exit_code == 0:
        return result
    # -2147217405 (cmd) or 2147749891 (Python) == (0x80041003) = Permission denied
    if exit_code in [-2147217405, 2147749891]:
        logger.warning('Don\'t have permission to get bitlocker drive status for {}.'.format(drive))
    # -1 is returned in cmd on drives without bitlocker suppprt (or as unsigned 2^32-1 = 4294967295 in Python)#
    elif exit_code in [-1, 4294967295]:
        logger.debug('Drive {} does not seem to have bitlocker protectors yet.'.format(drive))
    else:
        logger.warning('Cannot get bitlocker drive status for {}.'.format(drive))
        logger.warning('{}'.format(result))
    return None


def get_bitlocker_protection_key(drive: str) -> Union[str, None]:
    """
    Returns a string containing the protection key of a bitlocked drive
    """
    if not check_bitlocker_management_tools():
        return None
    # utf-8 produces less good results on latin alphabets, but better results on logographic / syllabic alphabets
    exit_code, result = command_runner('manage-bde -protectors {} -get'.format(drive), encoding='utf-8')
    if exit_code == 0:
        return result
    # -2147217405 (cmd) or 2147749891 (Python) == (0x80041003) = Permission denied
    if exit_code in [-2147217405, 2147749891]:
        logger.warning('Don\'t have permission to get bitlocker drive protectors for {}.'.format(drive))
    # -2147024809 (cmd) or 2147942487 (Python) == (0x80070057) = Incorrect parameter
    # This will happen on drives that aren't supposed to have bitlocker (FAT32, network drives, subst drives...)
    elif exit_code in [-2147024809, 2147942487]:
        logger.info('Drive {} is not supposed to have a bitlocker protecter.'.format(drive))
    # -1 is returned in cmd on valid drive without protectors (or as unsigned 2^32-1 = 4294967295 in Python)
    elif exit_code in [-1, 4294967295]:
        logger.debug('Drive {} does not seem to have bitlocker protectors yet.'.format(drive))
    # -2147024809 is returned on invalid drives (eg network drives, inexisting drives)
    else:
        logger.warning('Could not get bitlocker protector for drive {}: {}'.format(drive, result))
    return None


def get_bitlocker_status() -> dict:
    """
    Return bitlocker status for all drives
    """
    bitlocker_status = {}
    # Only NTFS / ReFS drives are allowed to have bitlocker
    for drive in get_logical_disks(include_fs=BITLOCKER_ELIGIBLE_FS, include_network_drives=False):
        bitlocker_status[drive] = get_bitlocker_drive_status(drive)
    return bitlocker_status


def get_bitlocker_keys() -> dict:
    """
    Return bitlocker protection keys for all drives
    """
    bitlocker_keys = {}
    for drive in get_logical_disks(include_fs=BITLOCKER_ELIGIBLE_FS, exclude_unknown_fs=False,
                                   include_network_drives=False):
        if get_bitlocker_drive_status(drive):
            bitlocker_keys[drive] = get_bitlocker_protection_key(drive)
    return bitlocker_keys


def get_bitlocker_full_status() -> dict:
    """
    Return full bitlocker status for all drives
    """
    bitlocker_full_status = {}
    for drive in get_logical_disks(include_fs=BITLOCKER_ELIGIBLE_FS, exclude_unknown_fs=False,
                                   include_network_drives=False):
        bitlocker_full_status[drive] = {'status': get_bitlocker_drive_status(drive),
                                        'protectors': get_bitlocker_protection_key(drive)
                                        }
    return bitlocker_full_status
