#! /usr/bin/env python
#  -*- coding: utf-8 -*-

# This file is part of windows_tools module

"""
Windows registry simple API

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'windows_tools.registry'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2019-2021 Orsiris de Jong'
__description__ = 'Windows registry 32 and 64 bits simple API'
__licence__ = 'BSD 3 Clause'
__version__ = '0.5.2'
__build__ = '2021052501'

from typing import List, NoReturn, Optional

# that import is needed so we get CONSTANTS from winreg (eg HKEY_LOCAL_MACHINE etc) for direct use in module
from winreg import *  # noqa ignore=F405
# The following lines make lint tools happy
from winreg import ConnectRegistry, OpenKey, EnumKey, EnumValue, QueryInfoKey, QueryValueEx, DeleteKey
from winreg import KEY_WOW64_32KEY, KEY_WOW64_64KEY, KEY_READ, KEY_ALL_ACCESS, HKEYType


def get_value(hive: int, key: str, value: Optional[str], arch: int = 0) -> str:
    """
    Returns a value from a given registry path

    :param hive: registry hive (windows.registry.HKEY_LOCAL_MACHINE...)
    :param key:  which registry key we're searching for
    :param value: which value we query, may be None if unnamed value is searched
    :param arch: which registry architecture we seek (0 = default, windows.registry.KEY_WOW64_64KEY, windows.registry.KEY_WOW64_32KEY)
                 Giving multiple arches here will return first result
    :return: value
    """

    def _get_value(hive: int, key: str, value: Optional[str], arch: int) -> str:
        try:
            open_reg = ConnectRegistry(None, hive)
            open_key = OpenKey(open_reg, key, 0, KEY_READ | arch)
            value, key_type = QueryValueEx(open_key, value)
            # Return the first match
            return value
        except (FileNotFoundError, TypeError, OSError) as exc:
            raise FileNotFoundError('Registry key [%s] with value [%s] not found. %s' % (key, value, exc))

    # 768 = 0 | KEY_WOW64_64KEY | KEY_WOW64_32KEY (where 0 = default)
    if arch == 768:
        for _arch in [KEY_WOW64_64KEY, KEY_WOW64_32KEY]:
            try:
                return _get_value(hive, key, value, _arch)
            except FileNotFoundError:
                pass
        raise FileNotFoundError
    else:
        return _get_value(hive, key, value, arch)


def get_values(hive: int, key: str, names: List[str], arch: int = 0, combine: bool = False) -> list:
    """
    Returns a dictionnary of values in names from registry key

    :param hive: registry hive (windows.registry.HKEY_LOCAL_MACHINE...)
    :param key: which registry key we're searching for
    :param names: which value names we query for
    :param arch: which registry architecture we seek (0 = default, windows.registry.KEY_WOW64_64KEY, windows.registry.KEY_WOW64_32KEY)
    :param combine: shall we combine multiple arch results or return first match
    :return: list of strings
    """

    def _get_values(hive: int, key: str, names: List[str], arch: int) -> list:
        try:
            open_reg = ConnectRegistry(None, hive)
            open_key = OpenKey(open_reg, key, 0, KEY_READ | arch)
            subkey_count, value_count, _ = QueryInfoKey(open_key)

            output = []
            for index in range(subkey_count):
                values = {}
                subkey_name = EnumKey(open_key, index)
                subkey_handle = OpenKey(open_key, subkey_name)
                for name in names:
                    try:
                        values[name] = QueryValueEx(subkey_handle, name)[0]
                    except (FileNotFoundError, TypeError):
                        pass
                output.append(values)
            return output

        except (FileNotFoundError, TypeError, OSError) as exc:
            raise FileNotFoundError('Cannot query registry key [%s]. %s' % (key, exc))

    # 768 = 0 | KEY_WOW64_64KEY | KEY_WOW64_32KEY (where 0 = default)
    if arch == 768:
        result = []
        for _arch in [KEY_WOW64_64KEY, KEY_WOW64_32KEY]:
            try:
                if combine:
                    result = result + (_get_values(hive, key, names, _arch))
                else:
                    return _get_values(hive, key, names, _arch)
            except FileNotFoundError:
                pass
        return result
    else:
        return _get_values(hive, key, names, arch)


OPEN_REGISTRY_HANDLE = None


def get_keys(hive: int, key: str, arch: int = 0, recursion_level: int = 1,
             filter_on_names: List[str] = None, combine: bool = False) -> dict:
    """
    :param hive: registry hive (windows.registry.HKEY_LOCAL_MACHINE...)
    :param key: which registry key we're searching for
    :param arch: which registry architecture we seek (0 = default, windows.registry.KEY_WOW64_64KEY, windows.registry.KEY_WOW64_32KEY)
    :param recursion_level: recursivity level
    :param filter_on_names: list of strings we search, if none given, all value names are returned
    :param combine: shall we combine multiple arch results or return first match
    :return: list of strings
    """

    global OPEN_REGISTRY_HANDLE

    def _get_keys(hive: int, key: str, arch: int, recursion_level: int, filter_on_names: List[str]):
        global OPEN_REGISTRY_HANDLE

        try:
            if not OPEN_REGISTRY_HANDLE:
                OPEN_REGISTRY_HANDLE = ConnectRegistry(None, hive)
            open_key = OpenKey(OPEN_REGISTRY_HANDLE, key, 0, KEY_READ | arch)
            subkey_count, value_count, _ = QueryInfoKey(open_key)

            output = {}
            values = []
            for index in range(value_count):
                name, value, type = EnumValue(open_key, index)
                if isinstance(filter_on_names, list) and name not in filter_on_names:
                    pass
                else:
                    values.append({'name': name, 'value': value, 'type': type})
            if not values == []:
                output[''] = values

            if recursion_level > 0:
                for subkey_index in range(subkey_count):
                    try:
                        subkey_name = EnumKey(open_key, subkey_index)
                        sub_values = get_keys(hive=0, key=key + '\\' + subkey_name, arch=arch,
                                              recursion_level=recursion_level - 1,
                                              filter_on_names=filter_on_names)
                        output[subkey_name] = sub_values
                    except FileNotFoundError:
                        pass

            return output

        except (FileNotFoundError, TypeError, OSError) as exc:
            raise FileNotFoundError('Cannot query registry key [%s]. %s' % (key, exc))

    # 768 = 0 | KEY_WOW64_64KEY | KEY_WOW64_32KEY (where 0 = default)
    if arch == 768:
        result = {}
        for _arch in [KEY_WOW64_64KEY, KEY_WOW64_32KEY]:
            try:
                if combine:
                    result.update(_get_keys(hive, key, _arch, recursion_level, filter_on_names))
                else:
                    return _get_keys(hive, key, _arch, recursion_level, filter_on_names)
            except FileNotFoundError:
                pass
        return result
    else:
        return _get_keys(hive, key, arch, recursion_level, filter_on_names)


def delete_sub_key(root_key: int, current_key: str, arch: int = 0) -> None:
    """

    :param root_key: winreg registry root key constant
    :param current_key:
    :param arch:
    :return:
    """

    def _delete_sub_key(root_key: int, current_key: str, arch: int) -> NoReturn:
        open_key = OpenKey(root_key, current_key, 0, KEY_ALL_ACCESS | arch)
        info_key = QueryInfoKey(open_key)
        for _ in range(0, info_key[0]):
            # NOTE:: This code is to delete the key and all sub_keys.
            # If you just want to walk through them, then
            # you should pass x to EnumKey. sub_key = EnumKey(open_key, x)
            # Deleting the sub_key will change the sub_key count used by EnumKey.
            # We must always pass 0 to EnumKey so we
            # always get back the new first sub_key.
            sub_key = EnumKey(open_key, 0)
            try:
                DeleteKey(open_key, sub_key)
            except OSError:
                _delete_sub_key(root_key, "\\".join([current_key, sub_key]), arch)
                # No extra delete here since each call
                # to delete_sub_key will try to delete itself when its empty.

        DeleteKey(open_key, "")
        open_key.Close()
        return

    # 768 = 0 | KEY_WOW64_64KEY | KEY_WOW64_32KEY (where 0 = default)
    if arch == 768:
        for _arch in [KEY_WOW64_64KEY, KEY_WOW64_32KEY]:
            _delete_sub_key(root_key, current_key, _arch)
    else:
        _delete_sub_key(root_key, current_key, arch)
