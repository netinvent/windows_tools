#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
wmi_queries wrapper and wmi timestamp converter
transforms wmi objects into python dicts
Handles most runtime errors

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'windows_tools.wmi_queries'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__description__ = 'Windows WMI query wrapper, wmi timezone converters'
__licence__ = 'BSD 3 Clause'
__version__ = '0.9.2'
__build__ = '2021031601'

import logging
import re
from datetime import datetime, timedelta
from logging.handlers import QueueHandler
# importing queues is only necessary for typing hints
# SimpleQueue does not exist in Python < 3.7
try:
    from queue import SimpleQueue, Queue
except ImportError:
    from queue import Queue
    from queue import Queue as SimpleQueue
from typing import Union

# imports to debug WMI requests with better error messages
import pywintypes
import wmi

logger = logging.getLogger()


def wmi_object_2_list_of_dict(wmi_objects, depth: int = 1, root: bool = True) -> Union[dict, list]:
    # Return a WMI object as a list of dicts, accepts multiple depth
    # Example for Win32_LoggedOnUser().Antecedent.AccountType return is [{'Antecedent': {'AccountType': 512}}]
    # Hence
    # wmi_handle.Win32_LoggedOnUser()[0].Antecedent.AccountType is equivalent of
    # res = wmi_object_2_list_of_dict(wmi_handle.Win32_LoggedOnUser(), 2)
    # res[0]['Antecedent']['AccountType']

    result = []

    if root is False:
        dictionnary = {}
        try:
            for attribute in wmi_objects.properties:
                try:
                    if depth > 1:
                        dictionnary[attribute] = wmi_object_2_list_of_dict(
                            getattr(wmi_objects, attribute), (depth - 1), root=False)
                    else:
                        dictionnary[attribute] = getattr(wmi_objects, attribute)
                except TypeError:
                    dictionnary[attribute] = None
            return dictionnary
        # wmi_object.properties might just be a string depending on the depth. Just return as is in that case
        except AttributeError:
            return wmi_objects

    for wmi_object in wmi_objects:
        dictionnary = {}
        for key in wmi_object.properties.keys():
            if depth <= 1:
                try:
                    dictionnary[key] = wmi_object.Properties_(key).Value
                except TypeError:
                    dictionnary[key] = None
            else:
                # noinspection PyBroadException
                try:
                    dictionnary[key] = wmi_object_2_list_of_dict(getattr(wmi_object, key), (depth - 1), root=False)
                # Some keys won't have attributes and trigger pywintypes.com_error and others. Need for bare except
                except Exception:
                    pass
        result.append(dictionnary)
    return result


def query_wmi(query_str: str, namespace: str = 'cimv2', name: str = 'noname', depth: int = 1,
              can_be_skipped: bool = False,
              mp_queue: Union[Queue, SimpleQueue] = None, debug: bool = False,
              computer: str = 'localhost') -> Union[list, None]:
    """
    Execute WMI queries that return pre-formatted python dictionnaries
    Also allows to pass a queue for logging retunrs when using multiprocessing
    """
    if mp_queue:
        logging_handler = QueueHandler(mp_queue)
        local_logger = logging.getLogger()
        local_logger.handlers = []
        local_logger.addHandler(logging_handler)
        if debug:
            local_logger.setLevel(logging.DEBUG)
        else:
            local_logger.setLevel(logging.INFO)
    else:
        local_logger = logging.getLogger()

    # Multiprocessing also requires to pickle results
    # Since we cannot send wmi objects, we'll convert them to dict first using wmi_object_2_list_of_dict

    # CoInitialize (and CoUninitialize) are needed when using WMI in threads, but not a multiprocessed childs
    # pythoncom.CoInitialize()
    logger.log(logging.DEBUG, 'Running WMI query [%s].' % name)
    # noinspection PyBroadException

    # Full moniker example
    # wmi_handle = wmi.WMI(moniker=r'winmgmts:{impersonationLevel=impersonate,authenticationLevel=pktPrivacy,(LockMemory, !IncreaseQuota)}!\\localhost\root\cimv2/Security/MicrosoftVolumeEncryption')
    try:
        if namespace.startswith('cimv2'):
            wmi_handle = wmi.WMI(
                moniker=r'winmgmts:{impersonationLevel=impersonate,authenticationLevel=pktPrivacy,(LockMemory, !IncreaseQuota)}!\\%s\root\%s' % (
                    computer, namespace))
            return wmi_object_2_list_of_dict(wmi_handle.query(query_str), depth)
        elif namespace == 'wmi':
            wmi_handle = wmi.WMI(namespace='wmi')
            return wmi_object_2_list_of_dict(wmi_handle.query(query_str), depth)
        elif namespace == 'SecurityCenter':
            # Try to fallback to securityCenter v1 for XP
            # noinspection PyBroadException
            try:
                wmi_handle = wmi.WMI(namespace='SecurityCenter2')
            except Exception:
                # noinspection PyBroadException
                try:
                    wmi_handle = wmi.WMI(namespace='SecurityCenter')
                except Exception:
                    logger.info('cannot get securityCenter handle.')
                    return None
            return wmi_object_2_list_of_dict(wmi_handle.query(query_str), depth)
        else:
            local_logger.critical('Bogus query path {}.'.format(namespace))
    except pywintypes.com_error:
        if can_be_skipped is not True:
            local_logger.log(logging.WARNING, 'Cannot get WMI query (pywin) {}.'.format(name), exc_info=True)
            local_logger.log(logging.DEBUG, 'Trace:', exc_info=True)
        else:
            local_logger.log(logging.INFO, 'Cannot get WMI query (pywin) {}.'.format(name))
    except wmi.x_access_denied:
        if can_be_skipped is not True:
            local_logger.log(logging.WARNING, 'Cannot get WMI request (access) {}.'.format(name), exc_info=True)
            local_logger.log(logging.DEBUG, 'Trace:', exc_info=True)
        else:
            local_logger.log(logging.INFO, 'Cannot get WMI request (access) {}.'.format(name))
    except NameError:
        if can_be_skipped is not True:
            local_logger.log(logging.WARNING, 'Cannot get WMI request (name) {}.'.format(name))
            local_logger.log(logging.DEBUG, 'Trace:', exc_info=True)
        else:
            local_logger.log(logging.INFO, 'Cannot get WMI query (name) {}.'.format(name))
    except Exception:
        if can_be_skipped is not True:
            local_logger.log(logging.WARNING, 'Cannot get WMI request (uncaught) {}.'.format(name), exc_info=True)
            local_logger.log(logging.DEBUG, 'Trace:', exc_info=True)
        else:
            local_logger.log(logging.INFO, 'Cannot get WMI request (uncaught) {}.'.format(name))
    return False

    # Only needed when used in threaded environment
    # finally:
    # pythoncom.CoUninitialize()


def get_wmi_timezone_bias() -> str:
    """
    Get current timezone bias in WMI compatible format, eg:
    "UTC+2" = "+120"

    :return: str
    """
    result = query_wmi(query_str='SELECT Bias FROM Win32_timezone', namespace='cimv2', name='timezonebias', depth=1,
                       can_be_skipped=False)
    try:
        return result[0]['Bias']
    except (KeyError, IndexError):
        logger.warning('Missing timezone bias info. Using UTC+0.')
        return "0"
    except TypeError:
        logger.warning('Missing timzeone bias. Using UTC+0.')
        return "0"


def datetime_to_cim_timestamp(timestamp: datetime) -> str:
    """
    Creates a WMI compatible timestamp from python datetime object
    """
    timezonebias = get_wmi_timezone_bias()
    cim_timestamp = timestamp.strftime('%Y%m%d%H%M%S.%f') + '+' + str(timezonebias)
    return cim_timestamp


def cim_timestamp_to_datetime(cim_timestamp: str, convert_to_utc: bool = True) -> datetime:
    """
    Convert WMI timestamp to python datetime object

    wmi timestamps ALWAYS include timestamp

    if utc_result is False, we'll return a datetime object of the current timezone
    """
    cim_time, cim_tz = re.split('[+-]', cim_timestamp)
    timestamp = datetime.strptime(cim_time, '%Y%m%d%H%M%S.%f')
    if convert_to_utc:
        if '+' in cim_timestamp:
            timestamp += timedelta(minutes=int(cim_tz))
        elif '-' in cim_timestamp:
            timestamp -= timedelta(minutes=int(cim_tz))
        # string representation
        # print(timestamp.strftime('%A, %B %d., %Y @ %X'))
    # else:
    # utc_sign = '+' if '+' in cim_timestamp else '-'
    # utc_offset = int(int(cim_tz)/60)
    # print(timestamp.strftime("%A, %B %d., %Y @ %X UTC{}{}".format(utc_sign, utc_offset)))
    return timestamp


def create_current_cim_timestamp(hour_offset: int = 0) -> str:
    """
    Creates a WMI compatible timestamp, like "20200818124602.499324+120" from
    current datetime
    Current datetime can be increased / decreased by specifing an offset

    :param hour_offset: adding an offset gives a offset hours in past timestamp
    :return: str: timestamp
    """
    timestamp = (datetime.utcnow() - timedelta(hours=hour_offset))
    return datetime_to_cim_timestamp(timestamp)
