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

__intname__ = 'tests.windows_tools.signtool'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__build__ = '2021020901'

from windows_tools.signtool import *

def test_signtool_path():
    signer = SignTool(certificate=None, pkcs12_password='None', authority_timestamp_url='http://timestamp.digicert.com')
    print('Path for x86 signtool', signer.detect_signtool('x86'))
    print('Path for x86 signtool', signer.detect_signtool('x64'))
    # We do not assert here since we won't have an SDK on the test machine


def test_signer():
    signer = SignTool(certificate=None, pkcs12_password='None', authority_timestamp_url='http://timestamp.digicert.com')
    try:
        signer.sign(r'c:\some-non-existing-executable.exe', 32)
    except AttributeError as exc:
        # AttributeError because we provided an empty authority timestamp url
        print('(NORMAL BEHAVIOR IN TESTS) Signing failed with: %s' % exc)
        assert True
    else:
        assert False


if __name__ == '__main__':
    print('Example code for %s, %s' % (__intname__, __build__))
    test_signtool_path()
    test_signer()
