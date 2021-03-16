#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
logical disk management

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'windows_tools.disks'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2018-2020 Orsiris de Jong'
__description__ = 'Logical disk (partition) management functions'
__licence__ = 'BSD 3 Clause'
__version__ = '0.1.1'
__build__ = '2021021501'

import os
from logging import getLogger

import psutil
import win32api

logger = getLogger()


def _get_logical_disks_plaintest():
    """
    This is a fallback solution when win32api failed
    Basic test against existing drive letters, also includes network drives
    """
    # Very basic test against existing paths
    drives = [chr(x) + ":" for x in range(65, 91) if os.path.exists(chr(x) + ":")]
    return drives


def _get_logical_disks_win32api(include_non_ntfs_refs: bool = False):
    """
    Returns \0 separated list of drives, eg r'C:\\0Z:\', also includes network drives
    """
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]

    if not include_non_ntfs_refs:
        filtered_drives = []
        for drive in drives:
            # volname, volsernum, maxfilenamlen, sysflags, filesystemtype = win32api.GetVolumeInformation(DrivePath)
            print('DRIVE: --{}--'.format(drive)) # WIP # TODO
            filesystem = win32api.GetVolumeInformation(drive)[4]
            if filesystem in ['NTFS', 'ReFS']:
                filtered_drives.append(drive)
        drives = filtered_drives

    # Remove antislash from drives
    drives = [drive.rstrip('\\') for drive in drives]
    return drives


def _get_logical_disks_psutil(include_non_ntfs_refs: bool = False):
    """
    Returns list of drives, does not include network drives
    """
    drps = psutil.disk_partitions()
    if not include_non_ntfs_refs:
        drives = [dp.device for dp in drps if dp.fstype == 'NTFS' or dp.fstype == 'ReFS']
    drives = [drive.rstrip('\\') for drive in drives]
    return drives


def get_logical_disks(include_network_drives: bool = False, include_non_ntfs_refs: bool = False):
    if include_network_drives:
        try:
            return _get_logical_disks_win32api(include_non_ntfs_refs=include_non_ntfs_refs)
        except Exception as exc:
            logger.warning('Cannot lisk disks via win32api: {}'.format(exc), exc_info=True)
    else:
        try:
            return _get_logical_disks_psutil(include_non_ntfs_refs=include_non_ntfs_refs)
        except Exception as exc:
            logger.warning('Cannot lisk disks via psutil: {}'.format(exc), exc_info=True)
    # Default fallback solution
    try:
        return _get_logical_disks_plaintest()
    except Exception as exc:
        logger.warning('Cannot lisk disks: {}'.format(exc), exc_info=True)

    return None
