#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Using windows signtool.exe to add authenticodes to executables

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "tests.windows_tools.signtool"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2024 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2024110701"

import os
import shutil
import random
import string


from windows_tools.powershell import PowerShellRunner
from windows_tools.signtool import *


def running_on_github_actions():
    """
    This is set in github actions workflow with
          env:
        RUNNING_ON_GITHUB_ACTIONS: true
    """
    return os.environ.get("RUNNING_ON_GITHUB_ACTIONS") == "true"  # bash 'true'


def pw_gen(size: int = 16, chars: list = string.ascii_letters + string.digits) -> str:
    return "".join(random.choice(chars) for _ in range(size))


def create_test_certificate():
    """
    Create a code signing certificate in order to make real signing tests
    Needs Windows 8.1+ (powershell 4.0) in order to work
    Older Win7 systems will fail this test because they rely on makecert.exe
    """

    # Github actions doesn't have a CERT:\ shortcut, so we'll fail with that test
    if running_on_github_actions():
        return None

    cert_location = os.path.join(
        os.environ.get("TEMP", r"C:\Windows\Temp"), "self_signed_test_authenticode.pfx"
    )
    dns_name = "acme.corp"
    password = pw_gen()

    create_command = r"$cert = New-SelfSignedCertificate -DnsName {} -Type CodeSigning -CertStoreLocation Cert:\CurrentUser\My".format(
        dns_name
    )
    pw_command = '$CertPassword = ConvertTo-SecureString -String "{}" -Force –AsPlainText'.format(
        password
    )
    export_command = r'Export-PfxCertificate -Cert "cert:\CurrentUser\My\$($cert.Thumbprint)" -FilePath "{}" -Password $CertPassword'.format(
        cert_location
    )
    full_command = "%s; if ($?) {%s}; if ($?) {%s}" % (
        create_command,
        pw_command,
        export_command,
    )

    PS = PowerShellRunner()
    exit_code, output = PS.run_command(full_command)
    if exit_code == 0:
        print(
            'Created test cert at {} with password "{}"'.format(cert_location, password)
        )
        return cert_location, password
    print("ERROR:", output)
    return None


def test_signtool_path():

    if running_on_github_actions():
        return None
    signer = SignTool(
        certificate=None,
        pkcs12_password="None",
        authority_timestamp_url="http://timestamp.digicert.com",
    )
    print("Path for x86 signtool", signer.detect_signtool("x86"))
    print("Path for x86 signtool", signer.detect_signtool("x64"))
    # We do not assert here since we won't have an SDK on the test machine


def test_signer():
    """
    Some signtool compatible timestamp URLs (as of 2021051401)

    http://timestamp.verisign.com/scripts/timstamp.dll
    http://timestamp.globalsign.com/scripts/timstamp.dll
    http://timestamp.comodoca.com/authenticode
    http://timestamp.digicert.com
    """

    if running_on_github_actions():
        return None
    cert, password = create_test_certificate()
    signer = SignTool(
        certificate=cert,
        pkcs12_password=password,
        authority_timestamp_url="http://timestamp.digicert.com",
    )

    # Let's copy then sign some executable, let's say cmd.exe
    # Using copyfile because we don't want metadata, permissions, buffer nor anything else
    source = os.path.join(
        os.environ.get("SYSTEMROOT", r"C:\Windows"), "system32", "cmd.exe"
    )
    destination = os.path.join(os.environ.get("TEMP", r"C:\Windows\Temp"), "cmd.exe")
    shutil.copyfile(source, destination)

    print("Now signing {}".format(destination))

    try:
        signer.sign(destination, 32)
    except AttributeError as exc:
        # AttributeError because we provided an empty authority timestamp url
        print("(NORMAL BEHAVIOR IN TESTS) Signing failed with: %s" % exc)
        assert (
            False
        ), "Failed to signe test executable with our superb self signed certificate"
    os.remove(destination)
    os.remove(cert)


if __name__ == "__main__":
    print("Example code for %s, %s" % (__intname__, __build__))
    test_signtool_path()
    test_signer()
