#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
Windows file_utils can be used to get / set ownership on files / directories,
set ACLs, and recursively set ownership or ALCsy
Functions have been tested on NTFS an ReFS (Win10 x64 2004)

From my post here: https://stackoverflow.com/a/61041460/2635443

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "windows_tools.file_utils"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020 Orsiris de Jong"
__description__ = "Windows NTFS & ReFS file ownership and ACL handling functions"
__licence__ = "BSD 3 Clause"
__version__ = "0.3.0"
__build__ = "2021021601"

import logging
from typing import Tuple, Union, List, Iterable

import ntsecuritycon
import pywintypes

# pywin32
import win32api
import win32security
from ofunctions.file_utils import get_paths_recursive

from windows_tools.users import get_pysid

logger = logging.getLogger(__intname__)


def get_ownership(path: str) -> Tuple[str, str, int]:
    """
    Returns owner from Path

    :param path: (str) path to directory / file to check
    :return: (tuple) ('owner', 'group', 'privilege')
    """
    try:
        sec_descriptor = win32security.GetFileSecurity(
            path, win32security.OWNER_SECURITY_INFORMATION
        )
        sid = sec_descriptor.GetSecurityDescriptorOwner()
        return win32security.LookupAccountSid(None, sid)
    except pywintypes.error as exc:
        # Let's raise OSError so we don't need to import pywintypes in parent module to catch the exception
        raise OSError("Cannot get owner of file: {0}. {1}".format(path, exc))


def take_ownership(path: str, owner=None, force: bool = True) -> bool:
    """
    Set owner on NTFS & ReFS files / directories, see
    https://stackoverflow.com/a/61009508/2635443

    :param path: (str) path
    :param owner: (PySID) object that represents the security identifier.
                  If not set, current security identifier will be used
    :param force: (bool) Shall we force take ownership
    :return:
    """
    try:
        hToken = win32security.OpenThreadToken(
            win32api.GetCurrentThread(), win32security.TOKEN_ALL_ACCESS, True
        )

    except win32security.error:
        hToken = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(), win32security.TOKEN_ALL_ACCESS
        )
    if owner is None:
        owner = win32security.GetTokenInformation(hToken, win32security.TokenOwner)
    prev_state = ()
    if force:
        new_state = [
            (
                win32security.LookupPrivilegeValue(None, name),
                win32security.SE_PRIVILEGE_ENABLED,
            )
            for name in (
                win32security.SE_TAKE_OWNERSHIP_NAME,
                win32security.SE_RESTORE_NAME,
            )
        ]
        prev_state = win32security.AdjustTokenPrivileges(hToken, False, new_state)
    try:
        sec_descriptor = win32security.SECURITY_DESCRIPTOR()
        sec_descriptor.SetSecurityDescriptorOwner(owner, False)
        win32security.SetFileSecurity(
            path, win32security.OWNER_SECURITY_INFORMATION, sec_descriptor
        )
    except pywintypes.error as exc:
        # Let's raise OSError so we don't need to import pywintypes in parent module to catch the exception
        raise OSError("Cannot take ownership of file: {0}. {1}.".format(path, exc))
    finally:
        if prev_state:
            win32security.AdjustTokenPrivileges(hToken, False, prev_state)
    return True


def take_ownership_recursive(path: str, owner=None) -> bool:
    """
    Recursive version of set_file_owner
    """

    def take_own(path):
        nonlocal owner
        try:
            take_ownership(path, owner=owner, force=True)
            return True
        except OSError:
            logger.error("Permission error on: {0}.".format(path))
            return False

    files = get_paths_recursive(path, fn_on_perm_error=take_own)

    result = True
    for file in files:
        res = take_ownership(file, force=True)
        if not res:
            result = False

    return result


def easy_permissions(permission):
    """
    Creates ntsecuritycon permission int bitmasks from simple RWX semmantics

    :param permission: (str) Simple R, RX, RWX, F  rights
    :return: (int) ntsecuritycon permission bitmask
    """
    permission = permission.upper()
    if permission == "R":
        return ntsecuritycon.GENERIC_READ
    if permission == "RX":
        return ntsecuritycon.GENERIC_READ | ntsecuritycon.GENERIC_EXECUTE
    if permission in ["RWX", "M"]:
        return (
            ntsecuritycon.GENERIC_READ
            | ntsecuritycon.GENERIC_WRITE
            | ntsecuritycon.GENERIC_EXECUTE
        )
    if permission == "F":
        return ntsecuritycon.GENERIC_ALL
    raise ValueError("Bogus easy permission")


def set_acls(
    path: str,
    user_list: Union[List[str], List[object]] = None,
    group_list: Union[List[str], List[object]] = None,
    owner: Union[str, object] = None,
    permissions: int = None,
    inherit: bool = False,
    inheritance: bool = False,
):
    """
    Set Windows DACL list

    ATTENTION: as of today, inherit=False copies the existing parent DACL list to the objects

    :param path: (str) path to directory/file
    :param user_sid_list: (list) str usernames or PySID objects
    :param group_sid_list: (list) str groupnames or PySID objects
    :param owner: (str) owner name or PySID obect
    :param permissions: (int) permission bitmask
    :param inherit: (bool) inherit parent permissions
    :param inheritance: (bool) apply ACL to sub folders and files
    """
    if inheritance:
        inheritance_flags = (
            win32security.CONTAINER_INHERIT_ACE | win32security.OBJECT_INHERIT_ACE
        )
    else:
        inheritance_flags = win32security.NO_INHERITANCE

    security_descriptor = {
        "AccessMode": win32security.GRANT_ACCESS,
        "AccessPermissions": 0,
        "Inheritance": inheritance_flags,
        "Trustee": {
            "TrusteeType": "",
            "TrusteeForm": win32security.TRUSTEE_IS_SID,
            "Identifier": "",
        },
    }

    # Now create a security descriptor for each user in the ACL list
    security_descriptors = []

    # If no user / group is defined, let's take current user
    if user_list is None and group_list is None:
        user_list = [get_pysid()]

    if user_list is not None:
        for sid in user_list:
            sid = get_pysid(sid)
            s = security_descriptor
            s["AccessPermissions"] = permissions
            s["Trustee"]["TrusteeType"] = win32security.TRUSTEE_IS_USER
            s["Trustee"]["Identifier"] = sid
            security_descriptors.append(s)

    if group_list is not None:
        for sid in group_list:
            sid = get_pysid(sid)
            s = security_descriptor
            s["AccessPermissions"] = permissions
            s["Trustee"]["TrusteeType"] = win32security.TRUSTEE_IS_GROUP
            s["Trustee"]["Identifier"] = sid
            security_descriptors.append(s)

    try:
        sec_descriptor = win32security.GetNamedSecurityInfo(
            path,
            win32security.SE_FILE_OBJECT,
            win32security.DACL_SECURITY_INFORMATION
            | win32security.UNPROTECTED_DACL_SECURITY_INFORMATION,
        )
    except pywintypes.error as exc:
        raise OSError("Failed to read security for file: {0}. {1}".format(path, exc))
    dacl = sec_descriptor.GetSecurityDescriptorDacl()
    dacl.SetEntriesInAcl(security_descriptors)

    security_information_flags = win32security.DACL_SECURITY_INFORMATION

    if not inherit:
        # PROTECTED_DACL_SECURITY_INFORMATION disables inheritance from parent
        security_information_flags = (
            security_information_flags
            | win32security.PROTECTED_DACL_SECURITY_INFORMATION
        )
    else:
        security_information_flags = (
            security_information_flags
            | win32security.UNPROTECTED_DACL_SECURITY_INFORMATION
        )

    # If we want to change owner, SetNamedSecurityInfo will need win32security.OWNER_SECURITY_INFORMATION in SECURITY_INFORMATION
    if owner is not None:
        security_information_flags = (
            security_information_flags | win32security.OWNER_SECURITY_INFORMATION
        )
        if isinstance(owner, str):
            owner = get_pysid(owner)

    try:
        # SetNamedSecurityInfo(path, object_type, security_information, owner, group, dacl, sacl)
        win32security.SetNamedSecurityInfo(
            path,
            win32security.SE_FILE_OBJECT,
            security_information_flags,
            owner,
            None,
            dacl,
            None,
        )
    except pywintypes.error as exc:
        raise OSError from exc


def get_paths_recursive_and_fix_permissions(
    path: str,
    owner: object = None,
    permissions: int = None,
    user_list: Union[List[str], List[object]] = None,
    **kwargs
) -> Iterable:
    """
    Allows all arguments from ofunctions.file_utils.get_paths_recursive()
    Works the same, except that while listing files and directories, we also fix permission issues
    """

    def fix_perms(path: str) -> None:
        nonlocal permissions
        nonlocal owner
        nonlocal user_list
        if not permissions:
            permissions = easy_permissions("F")
        logger.error("Permission error on: {0}.".format(path))
        try:
            set_acls(
                path,
                user_list=user_list,
                owner=owner,
                permissions=permissions,
                inheritance=False,
            )
        except OSError:
            # Lets force ownership change
            try:
                take_ownership(path, owner=owner, force=True)
                # Now try again
                set_acls(
                    path,
                    user_list=user_list,
                    owner=owner,
                    permissions=permissions,
                    inheritance=False,
                )
            except OSError as exc:
                logger.error("Cannot fix permission on {0}. {1}".format(path, exc))
                # Raise OSError since we cannot trust that the file list from get_files_recursive is complete
                raise OSError from OSError

    paths = get_paths_recursive(path, fn_on_perm_error=fix_perms, **kwargs)
    return paths
