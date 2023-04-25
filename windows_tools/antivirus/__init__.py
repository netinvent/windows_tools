#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
antivirus functions help to obtain Windows security antivirus state
Part of the deal is to read the antivirus product state via wmi which returns
a recimal value (ex: 397568). One converted to hexadecimal (ex: 0x61100), we can divide
that value into chunks to obtain antivirus product info:

0X 06   11   00
   |    |    |
   |    |    - Antivirus update status
   |    - Antivirus execution status
   - Product type


Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "windows_tools.antivirus"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2018-2020 Orsiris de Jong"
__description__ = "antivirus state and installed products retrieval"
__licence__ = "BSD 3 Clause"
__version__ = "0.7.3"
__build__ = "2023042501"

import re
from typing import List, Union

import windows_tools.installed_software
import windows_tools.wmi_queries

# Feel free to expand the antivirus vendor list
KNOWN_ANTIVIRUS_PRODUCTS_REGEX = [
    "avast",
    "avira",
    r"avg ?technologies",
    "bitdefender",
    r"dr\.?web",
    "eset",
    r"f-?secure",
    r"g ?data ?software",
    "kaspersky",
    "mcafee",
    "panda ?security",
    "sophos",
    r"trend ?micro",
    "malwarebytes",
    "vipre",
    "sentinel ?one",
]


def prepare_raw_state(raw_state: Union[int, str]) -> str:
    """
    Antivirus product or firewall product states given by securitycenter2 are numeric
    We need to convert them to hexadecimal and pad prefix zeros so we get 0x123456 length value
    we can actually use

    Formatter string

        {   # Format identifier
        0:  # first parameter
        #   # use "0x" prefix
        0   # fill with zeroes
        {1} # to a length of n characters (including 0x), defined by the second parameter
        x   # hexadecimal number, using lowercase letters for a-f
        }   # End of format identifier
    """
    state = "{0:#0{1}x}".format(int(raw_state), 8)
    if len(state) > 8:
        raise ValueError("Given state is too long.")
    return state


def securitycenter_get_product_type(raw_state: Union[int, str]) -> str:
    """
    Returns the antivirus / product type returned by securitycenter
    """
    state = prepare_raw_state(raw_state)
    return _securitycenter_get_product_type(state[-6:-4])


def _securitycenter_get_product_type(state: hex) -> str:
    return {
        "00": "None",
        "01": "Firewall",
        "02": "AutoUpdate Settings",
        "04": "Antivirus",
        "06": "Windows Defender / Security Essentials",  # This is a big assumption we make
        "08": "Antispyware",
        "16": "Internet Settings",
        "32": "UserAccount Control",
        "64": "Service",
    }.get(state, "Unknown")


def securitycenter_get_product_exec_state(raw_state: Union[int, str]) -> bool:
    """
    Returns the antivirus execution state as returned by securitycenter
    """
    state = prepare_raw_state(raw_state)
    return _securitycenter_get_product_exec_state(state[-4:-2])


def _securitycenter_get_product_exec_state(state: hex) -> bool:
    return {
        "00": False,  # Off
        "01": False,  # Expired
        "10": True,  # On
        "11": True,  # Snoozed
    }.get(state, "undefined")


def securitycenter_get_product_update_state(raw_state: Union[int, str]) -> bool:
    """
    Returns the antivirus update state as returned by securitycenter
    """
    state = prepare_raw_state(raw_state)
    return _securitycenter_get_product_update_state(state[-2:])


def _securitycenter_get_product_update_state(state: hex) -> bool:
    return {
        "00": True,  # UpToDate
        "01": False,  # OutOfDate
    }.get(state, "undefined")


def get_installed_antivirus_software() -> List[dict]:
    """
    Not happy with it either. But yet here we are... Thanks Microsoft for not having SecurityCenter2 on WinServers
    So we need to detect used AV engines by checking what is installed and do "best guesses"
    This test does not detect Windows defender since it's not an installed product
    """

    av_engines = []
    potential_seccenter_av_engines = []
    potential_av_engines = []

    result = windows_tools.wmi_queries.query_wmi(
        "SELECT * FROM AntivirusProduct",
        namespace="SecurityCenter",
        name="windows_tools.antivirus.get_installed_antivirus_software",
    )
    try:
        for product in result:
            av_engine = {
                "name": None,
                "version": None,
                "publisher": None,
                "enabled": None,
                "is_up_to_date": None,
                "type": None,
            }
            try:
                av_engine["name"] = product["displayName"]
            except KeyError:
                pass
            try:
                state = product["productState"]
                av_engine["enabled"] = securitycenter_get_product_exec_state(state)
                av_engine["is_up_to_date"] = securitycenter_get_product_update_state(
                    state
                )
                av_engine["type"] = securitycenter_get_product_type(state)
            except KeyError:
                pass
            potential_seccenter_av_engines.append(av_engine)
    # TypeError may happen when securityCenter namespace does not exist
    except (KeyError, TypeError):
        pass

    for product in windows_tools.installed_software.get_installed_software():
        product["enabled"] = None
        product["is_up_to_date"] = None
        product["type"] = None
        try:
            if re.search(
                r"anti.*(virus|viral)|malware", product["name"], re.IGNORECASE
            ):
                potential_av_engines.append(product)
                continue
            if re.search(
                r"|".join(KNOWN_ANTIVIRUS_PRODUCTS_REGEX),
                product["publisher"],
                re.IGNORECASE,
            ):
                potential_av_engines.append(product)
        # Specific case where name is unknown
        except KeyError:
            pass

    # SecurityCenter seems to be less precise than registry search
    # Now make sure we don't have "double entries" from securiycenter, then add them
    if len(potential_av_engines) > 0:
        for seccenter_engine in potential_seccenter_av_engines:
            for engine in potential_av_engines:
                print(seccenter_engine, engine)
                if seccenter_engine["name"] not in engine["name"]:
                    # Do not add already existing entries from securitycenter
                    av_engines.append(seccenter_engine)
    else:
        av_engines = potential_seccenter_av_engines

    av_engines = av_engines + potential_av_engines
    return av_engines
