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

__intname__ = "windows_tools.signtool"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2024 Orsiris de Jong"
__description__ = "Windows authenticode signature tool"
__licence__ = "BSD 3 Clause"
__version__ = "0.5.0"
__build__ = "2024090801"

import os
import sys

from typing import Optional, Union
from command_runner import command_runner
from ofunctions.file_utils import get_paths_recursive
from ofunctions.network import check_http_internet
from windows_tools.bitness import is_64bit, is_64bit_executable


CURRENT_EXECUTABLE = os.path.abspath(sys.argv[0])
CURRENT_DIR = os.path.dirname(CURRENT_EXECUTABLE)
dont_sign_file = os.path.join(CURRENT_DIR, "signtool.err.log")

# Basic PATHS where signtool.exe should reside when Windows SDK is installed
if is_64bit():
    SDK_PROGRAM_FILES = os.environ.get("PROGRAMFILES(X86)", "c:/Program Files (x86)")
else:
    SDK_PROGRAM_FILES = os.environ.get("PROGRAMFILES", "C:/Program Files")
WINDOWS_SDK_BASE_PATH = os.path.join(SDK_PROGRAM_FILES, "Windows Kits")


# SIGNTOOL_EXECUTABLE_32 = 'c:/Program Files (x86)/Windows Kits/10/bin/10.0.19041.0/x86/signtool.exe'
# SIGNTOOL_EXECUTABLE_64 = 'c:/Program Files (x86)/Windows Kits/10/bin/10.0.19041.0/x64/signtool.exe'


class SignTool:
    """
    Microsoft Windows Authenticode Signing

    Needs Windows SDK installed into 'c:/Program Files (x86)/Windows Kits' that comes with signtool.exe
    signtool.exe path will be probed per arch, and can be overriden using SIGNTOOL_X32 and SIGNTOOL_X64
    environment variables

    Usage:

    with PKCS12 file
    signer = SignTool(pkcs12_certificate, pkcs12_password, 'https://url_of_signing_auth', sdk_winver = 10)
    signer.sign("c:\\path\\to\\executable", 64)

    without USB security Token
    signer = SignTool()
    signer.sign("c:\\path\\to\\executable", 64)

    With USB security token automation
    signer = SignTool(pkcs12_certificate, pkcs12_password, "https://url_of_timestamp_auth", container_name="my_ev_container", cryptographic_provider="my_cryptographic_provider)

    """

    def __init__(
        self,
        certificate: Optional[str] = None,
        pkcs12_password: Optional[str] = None,
        authority_timestamp_url: Optional[str] = None,
        sdk_winver: Optional[int] = 10,
        container_name: Optional[str] = None,
        cryptographic_provider: Optional[str] = None,
    ):
        self.certificate = certificate
        self.pkcs12_password = pkcs12_password
        if authority_timestamp_url:
            self.authority_timestamp_url = authority_timestamp_url
        else:
            self.get_timestamp_server()
        self.sdk_winver = sdk_winver
        self.container_name = container_name
        self.cryptographic_provider = cryptographic_provider

    def detect_signtool(self, arch: str):
        """
        Try to detect the latest signtool.exe that comes with Windows SDK
        """

        # Get base path ie c:\Program Files (x86)\Windows Kits\{version}
        sdk_base_dir = get_paths_recursive(
            WINDOWS_SDK_BASE_PATH,
            d_include_list=["{}".format(self.sdk_winver)],
            exclude_files=True,
            min_depth=2,
            max_depth=2,
        )
        if not sdk_base_dir:
            return None

        # Get all sdk version paths ie c:\Program Files (x86)\Windows Kits\{version}\bin\{sdk_versions}
        sdk_dirs = get_paths_recursive(
            os.path.join(next(sdk_base_dir), "bin"),
            d_include_list=["{}*".format(self.sdk_winver)],
            exclude_files=True,
            min_depth=2,
            max_depth=2,
        )

        # Get most recent SDK directory
        try:
            sdk_dir = sorted(sdk_dirs, reverse=True)[0]
        except IndexError:
            return None

        return next(
            get_paths_recursive(
                sdk_dir,
                d_include_list=[arch],
                f_include_list=["signtool.exe"],
                exclude_dirs=True,
            )
        )

    def get_timestamp_server(self):
        """
        If no timestamp server is specified, use one of those,
        see https://engineertips.wordpress.com/2019/08/22/timestamp-server-list-for-signtool/
        """

        ts_servers = [
            "http://timestamp.digicert.com",
            "http://timestamp.sectigo.com",
            "http://timestamp.globalsign.com/scripts/timstamp.dll",
        ]
        for server in ts_servers:
            if check_http_internet([server]):
                self.authority_timestamp_url = server
                return True
        raise ValueError("No online timeserver found")

    def sign(
        self, executable, bitness: Union[None, int, str] = None, dry_run: bool = False
    ):
        if not bitness:
            possible_bitness = is_64bit_executable(executable)
            if possible_bitness is not None:
                bitness = 64 if possible_bitness else 32
        if bitness in [32, "32", "x86"]:
            signtool = os.environ.get("SIGNTOOL_X32", self.detect_signtool("x86"))
        elif bitness in [64, "64", "x64"]:
            signtool = os.environ.get("SIGNTOOL_X64", self.detect_signtool("x64"))
        else:
            if not bitness:
                raise ValueError(
                    "Cannot autodetect bitness. Please specify bitness or install win32file"
                )
            else:
                raise ValueError("Bogus bitness.")

        if not os.path.exists(signtool):
            raise EnvironmentError("Could not find valid signtool.exe")

        cmd = "{} sign -tr {} -td sha256 -fd sha256".format(
            signtool, self.authority_timestamp_url
        )
        if self.certificate:
            cmd += " -f {}".format(self.certificate)
            if self.container_name:
                cmd += ' -kc "[{{{{{}}}}}]={}"'.format(
                    self.pkcs12_password, self.container_name
                )
            elif self.pkcs12_password:
                cmd += " -p {}".format(self.pkcs12_password)
        if self.cryptographic_provider:
            cmd += ' -csp "{}"'.format(self.cryptographic_provider)
        cmd += ' "{}"'.format(executable)

        if dry_run:
            print("DRY RUN: {}".format(cmd))
            return True
        else:
            # Make sure we don't sign automatically in order to prevent an EV certificate token to be blocked because of bogus password attempts
            if os.path.isfile(dont_sign_file) and self.container_name:
                raise EnvironmentError(
                    "File {} exists which says signature had errors. Won't sign anything unless file is deleted and issue resolved".format(
                        dont_sign_file
                    )
                )
            result, output = command_runner(cmd)
            if result == 0:
                return True
            else:
                # Make sure we create a tmp file that unless deleted, won't sign executables again
                with open(dont_sign_file, "w") as fp:
                    fp.write(
                        "NO SIGNATURE BECAUSE last cmd {} exited with {}:{}".format(
                            cmd, result, output
                        )
                    )
                raise AttributeError(
                    "Cannot sign executable file [%s] with signtool.exe. Command output\n%s"
                    % (executable, output)
                )
