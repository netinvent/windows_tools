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
__description__ = 'Simple virtualization platform identification for Windows guest'
__licence__ = 'BSD 3 Clause'
__version__ = '0.3.2'
__build__ = '2021070201'


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

        result = windows_tools.wmi_queries.query_wmi('SELECT Manufacturer, Model FROM Win32_ComputerSystem',
                                                     name='windows_tools.virtualization.get_relavant_platform_info_1')
        try:
            product_id['computersystem'] = result[0]
        except IndexError:
            pass

        result = windows_tools.wmi_queries.query_wmi('SELECT Manufacturer, Product FROM Win32_Baseboard',
                                                     name='windows_tools.virtualization.get_relavant_platform_info_2')
        try:
            product_id['baseboard'] = result[0]
        except IndexError:
            pass

        result = windows_tools.wmi_queries.query_wmi('SELECT Manufacturer, SerialNumber, Version FROM Win32_Bios',
                                                     name='windows_tools.virtualization.get_relavant_platform_info_3')
        try:
            product_id['bios'] = result[0]
        except IndexError:
            pass

        result = windows_tools.wmi_queries.query_wmi('SELECT Caption, Model, SerialNumber FROM Win32_DiskDrive',
                                                     name='windows_tools.virtualization.get_relavant_platform_info_4')
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
                virt_products = ['oVirt', 'VBOX', 'VMWare', 'Hyper-V', 'Xen', 'KVM', 'qemu', 'bochs', 'VRTUAL']
                for virt_product in virt_products:
                    if re.search(virt_product, product_id[key][sub_key], re.IGNORECASE):
                        # Thanks Microsoft, fuzzy detection
                        if virt_product == 'VRTUAL':
                            virt_product = 'Hyper-V'
                        return True, virt_product
    return False, 'Physical / Unknown hypervisor'
