#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
virtualization identification

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'windows_tools.virtualization'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.3.0'
__build__ = '2021021701'


from typing import Tuple
from logging import getLogger
import re
import windows_tools.wmi_queries


logger = getLogger()


def get_relevant_platform_info() -> dict:
    product_id = {}

    # noinspection PyBroadException
    try:
        # Create a list of various computer data which will allow to check if we're running on a virtual system

        result = windows_tools.wmi_queries.query_wmi('SELECT Manufacturer, Model FROM Win32_ComputerSystem')
        try:
            product_id['computersystem'] = result[0]
        except IndexError:
            pass

        result = windows_tools.wmi_queries.query_wmi('SELECT Manufacturer, Product FROM Win32_Baseboard')
        try:
            product_id['baseboard'] = result[0]
        except IndexError:
            pass

        result = windows_tools.wmi_queries.query_wmi('SELECT Manufacturer, SerialNumber, Version FROM Win32_Bios')
        try:
            product_id['bios'] = result[0]
        except IndexError:
            pass

        result = windows_tools.wmi_queries.query_wmi('SELECT SerialNumber FROM Win32_DiskDrive')
        try:
            product_id['diskdrive'] = result[0]
        except IndexError:
            pass
    except Exception:
        logger.error('Cannot perform virtualization check.')

    return product_id


def check_for_virtualization(product_id: dict) -> Tuple[bool, str]:
    """
    Tries to find hypervisors, needs various WMI results as argument, ie:
    product_id = {'computersystem': {'Manufacturer': 'xx', 'Model': 'YY'},
                  'baseboard': {'Manufacturer': 'xx', 'Product': 'yy'},
                  'bios': {'Manufacturer': 'xx', 'SerialNumber': '1234', 'Version': 'zz'}
                  }

    :param product_id list of strings that come from various checks above

    Basic detection
    Win32_ComputerSystem.Model could contain 'KVM'
    Win32_BIOS.Manufacturer could contain 'XEN'
    Win32_BIOS.SMBIOSBIOSVersion could contain 'VBOX', 'bochs', 'qemu', 'VirtualBox', 'VMWare' or 'Hyper-V'

    ovirt adds oVirt to Win32_computersystem.Manufacturer (tested on Win7 oVirt 4.2.3 guest)
    HyperV may add 'Microsoft Corporation' to Win32_baseboard.Manufacturer
        and 'Virtual Machine' to Win32_baseboard.Product (tested on Win2012 R2 guest/host)
    HyperV may add 'VERSION/ VRTUAL' to Win32_BIOS.SMBIOSBIOSVersion (tested on Win2012 R2 guest/host)
        (yes, the error to 'VRTUAL' is real)
    VMWare adds 'VMWare to Win32_BIOS.SerialNumber (tested on Win2012 R2 guest/ VMWare ESXI 6.5 host)
    Xen adds 'Xen' to Win32_BIOS.Version (well hopefully)
    """

    for key in product_id:
        for sub_key in product_id[key]:
            if isinstance(product_id[key][sub_key], str):
                # First try to detect oVirt before detecting Qemu/KVM
                if re.search('oVirt', product_id[key][sub_key], re.IGNORECASE):
                    return True, 'oVirt'
                if re.search('VBOX', product_id[key][sub_key], re.IGNORECASE):
                    return True, 'VirtualNox'
                if re.search('VMWare', product_id[key][sub_key], re.IGNORECASE):
                    return True, 'VMWare'
                if re.search('Hyper-V', product_id[key][sub_key], re.IGNORECASE):
                    return True, 'Hyper-V'
                if re.search('Xen', product_id[key][sub_key], re.IGNORECASE):
                    return True, 'Xen'
                if re.search('KVM', product_id[key][sub_key], re.IGNORECASE):
                    return True, 'KVM'
                if re.search('qemu', product_id[key][sub_key], re.IGNORECASE):
                    return True, 'qemu'
                if re.search('bochs', product_id[key][sub_key], re.IGNORECASE):
                    return True, 'bochs'
                # Fuzzy detection
                if re.search('VRTUAL', product_id[key][sub_key], re.IGNORECASE):
                    return True, 'HYPER-V'
    return False, 'Physical / Unknown hypervisor'
