#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
Using windows signtool.exe to add authenticodes to executables

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'windows_tools.signtool'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__description__ = 'Windows authenticode signature tool'
__licence__ = 'BSD 3 Clause'
__version__ = '0.2.0'
__build__ = '2021051201'

import os

from command_runner import command_runner
from ofunctions.file_utils import get_paths_recursive

# Basic PATHS where signtool.exe should reside when Windows SDK is installed
WINDOWS_SDK_BASE_PATH = 'c:/Program Files (x86)/Windows Kits'


# SIGNTOOL_EXECUTABLE_32 = 'c:/Program Files (x86)/Windows Kits/10/bin/10.0.19041.0/x86/signtool.exe'
# SIGNTOOL_EXECUTABLE_64 = 'c:/Program Files (x86)/Windows Kits/10/bin/10.0.19041.0/x64/signtool.exe'


class SignTool:
    """
    Microsoft Windows Authenticode Signing

    Needs Windows SDK installed into 'c:/Program Files (x86)/Windows Kits' that comes with signtool.exe
    signtool.exe path will be probed per arch, and can be overriden using SIGNTOOL_X32 and SIGNTOOL_X64
    environment variables

    Usage:

    signer = SignTool(pkcs12_certificate, pkcs12_password, 'https://url_of_signing_auth', sdk_winver = 10)

    """

    def __init__(self, certificate, pkcs12_password: str, authority_timestamp_url: str, sdk_winver: int = 10):
        self.certificate = certificate
        self.pkcs12_password = pkcs12_password
        self.authority_timestamp_url = authority_timestamp_url
        self.sdk_winver = sdk_winver

    def detect_signtool(self, arch: str):
        """
        Try to detect the latest signtool.exe that comes with Windows SDK
        """

        # Get base path ie c:\Program Files (x86)\Windows Kits\{version}
        sdk_base_dir = get_paths_recursive(WINDOWS_SDK_BASE_PATH,
                                           d_include_list=['{}'.format(self.sdk_winver)],
                                           exclude_files=True,
                                           min_depth=2, max_depth=2)
        if not sdk_base_dir:
            return None

        # Get all sdk version paths ie c:\Program Files (x86)\Windows Kits\{version}\bin\{sdk_versions}
        sdk_dirs = get_paths_recursive(os.path.join(next(sdk_base_dir), 'bin'),
                                       d_include_list=['{}*'.format(self.sdk_winver)],
                                       min_depth=2, max_depth=2)

        # Get most recent SDK directory
        try:
            sdk_dir = sorted(sdk_dirs, reverse=True)[0]
        except IndexError:
            return None

        return next(
            get_paths_recursive(sdk_dir, d_include_list=[arch], f_include_list=['signtool.exe'], exclude_dirs=True))

    def sign(self, executable, bitness: int):
        if bitness == 32:
            signtool = os.environ.get('SIGNTOOL_X32', self.detect_signtool('x86'))
        elif bitness == 64:
            signtool = os.environ.get('SIGNTOOL_X64', self.detect_signtool('x64'))
        else:
            raise ValueError('Bogus bitness.')

        if not os.path.exists(signtool):
            raise EnvironmentError('Could not find valid signtool.exe')

        result, output = command_runner(
            '"%s" sign /tr %s /td sha256 /fd sha256 /f "%s" /p %s "%s"' %
            (signtool, self.authority_timestamp_url, self.certificate, self.pkcs12_password, executable))

        if result == 0:
            return True
        else:
            raise AttributeError(
                'Cannot sign executable file [%s] with signtool.exe. Command output\n%s' % (executable, output))
