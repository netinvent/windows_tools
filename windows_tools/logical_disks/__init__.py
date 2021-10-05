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

__intname__ = "windows_tools.logical_disks"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2018-2020 Orsiris de Jong"
__description__ = "Logical disk (partition) management functions"
__licence__ = "BSD 3 Clause"
__version__ = "1.0.0"
__build__ = "2021060201"

import os
from logging import getLogger

import psutil
import win32api

logger = getLogger(__intname__)


def _get_logical_disks_plaintest():
    """
    This is a fallback solution when win32api failed
    Basic test against existing drive letters, also includes network drives
    """
    # Very basic test against existing paths
    drives = [chr(x) + ":" for x in range(65, 91) if os.path.exists(chr(x) + ":")]
    return drives


def _get_logical_disks_win32api(
    include_fs: list = None, exclude_unknown_fs: bool = False
):
    """
    include_fs: list of which filesystems to include, example ['NTFS', 'ReFS']
    exclude_unknown_fs: shall we exclude unknown filesystems
    Returns list of drives, does include network drives

    GetLogicalDriveStrings Returns \0 separated list of drives, eg r'C:\\0Z:\', also includes network drives
    """
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split("\000")[:-1]

    if include_fs:
        filtered_drives = []
        for drive in drives:
            # volname, volsernum, maxfilenamlen, sysflags, filesystemtype = win32api.GetVolumeInformation(DrivePath)
            # We may have floppy drives (eg: A:) in drives list, especially for virtualized platforms
            # so win32api.GetVolumeInformation(drive) would fail with
            # pywintypes.error: (21, 'GetVolumeInformation', 'The device is not ready.')
            try:
                filesystem = win32api.GetVolumeInformation(drive)[4]
                if filesystem in include_fs:
                    filtered_drives.append(drive)
            # We'll use bare exception here because pywintypes exceptions aren't always used
            except Exception as exc:  # pylint: disable=W0702
                if not exclude_unknown_fs:
                    filtered_drives.append(drive)
        drives = filtered_drives

    # Remove antislash from drives
    drives = [drive.rstrip("\\") for drive in drives]
    return drives


def _get_logical_disks_psutil(
    include_fs: list = None, exclude_unknown_fs: bool = False
):
    """
    include_fs: list of which filesystems to include, example ['NTFS', 'ReFS']
    exclude_unknown_fs: shall we exclude unknown filesystems
    Returns list of drives, does not include network drives
    """
    drps = psutil.disk_partitions()
    drives = []
    for dp in drps:
        if include_fs:
            if dp.fstype in include_fs:
                drives.append(dp.device)
            elif not exclude_unknown_fs and dp.fstype == "":
                drives.append(dp.device)
        else:
            drives.append(dp.device)
    drives = [drive.rstrip("\\") for drive in drives]
    return drives


def get_logical_disks(
    include_fs: list = None,
    exclude_unknown_fs: bool = False,
    include_network_drives: bool = True,
):
    if include_network_drives:
        try:
            return _get_logical_disks_win32api(
                include_fs=include_fs, exclude_unknown_fs=exclude_unknown_fs
            )
        except Exception as exc:
            logger.warning(
                "Cannot lisk disks via win32api: {}".format(exc), exc_info=True
            )
    else:
        try:
            return _get_logical_disks_psutil(
                include_fs=include_fs, exclude_unknown_fs=exclude_unknown_fs
            )
        except Exception as exc:
            logger.warning(
                "Cannot lisk disks via psutil: {}".format(exc), exc_info=True
            )
    # Default fallback solution
    try:
        return _get_logical_disks_plaintest()
    except Exception as exc:
        logger.warning("Cannot lisk disks: {}".format(exc), exc_info=True)

    return None
