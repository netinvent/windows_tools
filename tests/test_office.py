#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
Microsoft Office identification

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "tests.windows_tools.office"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2020-2024 Orsiris de Jong"
__licence__ = "BSD 3 Clause"
__build__ = "2021021601"

from windows_tools.office import *


def test_get_office_version():
    """
    This is a bogus test that probably will not work on test machines without office installed
    Hence we allow None as return value too, rendering the test not very useful
    """

    office_version, click_and_run = get_office_version()
    print("Office version detected: {} {}".format(office_version, click_and_run))
    assert office_version in list(KNOWN_VERSIONS.values()) + [
        "2016",
        "2019",
        "O365",
        None,
    ], "Bogus office version detected"


if __name__ == "__main__":
    print("Example code for %s, %s" % (__intname__, __build__))
    test_get_office_version()
