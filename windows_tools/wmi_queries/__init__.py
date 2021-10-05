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

__intname__ = "windows_tools.wmi_queries"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2021 Orsiris de Jong"
__description__ = "Windows WMI query wrapper, wmi timezone converters"
__licence__ = "BSD 3 Clause"
__version__ = "0.9.7"
__build__ = "2021070201"

import logging
import re
from datetime import datetime, timedelta, timezone
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

logger = logging.getLogger(__intname__)


def wmi_object_2_list_of_dict(
    wmi_objects, depth: int = 1, root: bool = True
) -> Union[dict, list]:
    """
    Return a WMI object as a list of dicts, accepts multiple depth
    Example for Win32_LoggedOnUser().Antecedent.AccountType return is [{'Antecedent': {'AccountType': 512}}]
    Hence
    wmi_handle.Win32_LoggedOnUser()[0].Antecedent.AccountType is equivalent of
    res = wmi_object_2_list_of_dict(wmi_handle.Win32_LoggedOnUser(), 2)
    res[0]['Antecedent']['AccountType']
    """

    result = []

    if root is False:
        dictionary = {}
        try:
            for attribute in wmi_objects.properties:
                try:
                    if depth > 1:
                        dictionary[attribute] = wmi_object_2_list_of_dict(
                            getattr(wmi_objects, attribute), (depth - 1), root=False
                        )
                    else:
                        dictionary[attribute] = getattr(wmi_objects, attribute)
                except TypeError:
                    dictionary[attribute] = None
            return dictionary
        # wmi_object.properties might just be a string depending on the depth. Just return as is in that case
        except AttributeError:
            return wmi_objects

    for wmi_object in wmi_objects:
        dictionary = {}
        for key in wmi_object.properties.keys():
            if depth <= 1:
                try:
                    dictionary[key] = wmi_object.Properties_(key).Value
                except TypeError:
                    dictionary[key] = None
            else:
                # noinspection PyBroadException
                try:
                    dictionary[key] = wmi_object_2_list_of_dict(
                        getattr(wmi_object, key), (depth - 1), root=False
                    )
                # Some keys won't have attributes and trigger pywintypes.com_error and others. Need for bare except
                except Exception:
                    pass
        result.append(dictionary)
    return result


def query_wmi(
    query_str: str,
    namespace: str = "cimv2",
    name: str = "noname",
    depth: int = 1,
    can_be_skipped: bool = False,
    mp_queue: Union[Queue, SimpleQueue] = None,
    debug: bool = False,
    computer: str = "localhost",
) -> Union[list, None]:
    """
    Execute WMI queries that return pre-formatted python dictionaries
    Also allows to pass a queue for logging returns when using multiprocessing
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
        local_logger = logging.getLogger(__intname__)

    # Multiprocessing also requires to pickle results
    # Since we cannot send wmi objects, we'll convert them to dict first using wmi_object_2_list_of_dict

    # CoInitialize (and CoUninitialize) are needed when using WMI in threads, but not a multiprocessing child
    # pythoncom.CoInitialize()
    local_logger.debug("Running WMI query [%s]." % name)
    # noinspection PyBroadException

    # Full moniker example
    # wmi_handle = wmi.WMI(moniker=r'winmgmts:{impersonationLevel=impersonate,authenticationLevel=pktPrivacy,(LockMemory, !IncreaseQuota)}!\\localhost\root\cimv2/Security/MicrosoftVolumeEncryption')
    try:
        if namespace.startswith("cimv2"):
            wmi_handle = wmi.WMI(
                moniker=r"winmgmts:{impersonationLevel=impersonate,authenticationLevel=pktPrivacy,(LockMemory, !IncreaseQuota)}!\\%s\root\%s"
                % (computer, namespace)
            )
            return wmi_object_2_list_of_dict(wmi_handle.query(query_str), depth)
        elif namespace == "wmi":
            wmi_handle = wmi.WMI(namespace="wmi")
            return wmi_object_2_list_of_dict(wmi_handle.query(query_str), depth)
        elif namespace == "SecurityCenter":
            # Try to fallback to securityCenter v1 for XP
            # noinspection PyBroadException
            try:
                wmi_handle = wmi.WMI(namespace="SecurityCenter2")
            except Exception:
                # noinspection PyBroadException
                try:
                    wmi_handle = wmi.WMI(namespace="SecurityCenter")
                except Exception:
                    logger.info("cannot get securityCenter handle.")
                    return None
            return wmi_object_2_list_of_dict(wmi_handle.query(query_str), depth)
        else:
            local_logger.critical("Bogus query path {}.".format(namespace))
    except pywintypes.com_error:
        if can_be_skipped is not True:
            local_logger.warning(
                "Cannot get WMI query (pywin) {}.".format(name), exc_info=True
            )
            local_logger.debug("Trace:", exc_info=True)
        else:
            local_logger.info("Cannot get WMI query (pywin) {}.".format(name))
    except wmi.x_access_denied:
        if can_be_skipped is not True:
            local_logger.warning(
                "Cannot get WMI request (access) {}.".format(name), exc_info=True
            )
            local_logger.debug("Trace:", exc_info=True)
        else:
            local_logger.info("Cannot get WMI request (access) {}.".format(name))
    except wmi.x_wmi:
        if can_be_skipped is not True:
            local_logger.warning(
                "Cannot get WMI query (x_wmi) {}.".format(name), exc_info=True
            )
            local_logger.debug("Trace:", exc_info=True)
        else:
            local_logger.info("Cannot get WMI query (x_wmi) {}.".format(name))
    except NameError:
        if can_be_skipped is not True:
            local_logger.warning("Cannot get WMI request (name) {}.".format(name))
            local_logger.debug("Trace:", exc_info=True)
        else:
            local_logger.info("Cannot get WMI query (name) {}.".format(name))
    except Exception:
        if can_be_skipped is not True:
            local_logger.warning(
                "Cannot get non skippable WMI request (uncaught) {}.".format(name)
            )
            local_logger.debug("Trace:", exc_info=True)
        else:
            local_logger.info("Cannot get WMI request (uncaught) {}.".format(name))
    return None

    # Only needed when used in threaded environment
    # finally:
    # pythoncom.CoUninitialize()


def get_wmi_timezone_bias() -> str:
    """
    Get current timezone bias in WMI compatible format, eg:
    "UTC+2" = "+120"

    :return: str
    """
    result = query_wmi(
        query_str="SELECT Bias FROM Win32_timezone",
        namespace="cimv2",
        name="windows_tools.wmi_queries.timezonebias",
        depth=1,
        can_be_skipped=False,
    )
    try:
        return result[0]["Bias"]
    except (KeyError, IndexError):
        logger.warning("Missing timezone bias info. Using UTC+0.")
        return "0"
    except TypeError:
        logger.warning("Missing timzeone bias. Using UTC+0.")
        return "0"


def utc_datetime_to_cim_timestamp(dt: datetime, localize: bool = True) -> str:
    """
    Creates a WMI compatible timestamp from python datetime object
    """
    if localize:
        timezonebias = get_wmi_timezone_bias()
    else:
        timezonebias = 0

    cim_timestamp = dt.strftime("%Y%m%d%H%M%S.%f") + "+" + str(timezonebias)
    return cim_timestamp


def cim_timestamp_to_datetime(cim_timestamp: str, utc: bool = True) -> datetime:
    """
    Convert WMI timestamp to python datetime object

    wmi timestamps ALWAYS include timezones, hence are always UTC

    if utc is False, we'll return a datetime object without current timezone
    """
    cim_time, cim_offset = re.split("[+-]", cim_timestamp)
    timestamp = datetime.strptime(cim_time, "%Y%m%d%H%M%S.%f")

    if "+" in cim_timestamp:
        offset = int(cim_offset)
    elif "-" in cim_timestamp:
        offset = -int(cim_offset)

    if utc:
        timestamp = timestamp.replace(tzinfo=timezone(timedelta(minutes=offset)))
    else:
        timestamp += timedelta(minutes=offset)
    return timestamp


def create_cim_timestamp_from_now(**kwargs) -> str:
    """
    Creates a WMI compatible timestamp, like "20200818124602.499324+120" from
    current datetime
    Current datetime can be increased / decreased by specifing an offset

    Future timestamps are achieved by specifying positive values, eg days=1
    Past timestamps are achieved by specifying negative values, eg days=-1

    Accepts all kwargs that timedelta accepts
    """
    dt = datetime.utcnow() + timedelta(**kwargs)
    return utc_datetime_to_cim_timestamp(dt)


def create_current_cim_timestamp(hour_offset: int = 0) -> str:  # COMPAT <0.9.5
    """
    Compatibility wrapper for create_cim_timestamp_from_now
    """
    return create_cim_timestamp_from_now(hours=-hour_offset)
