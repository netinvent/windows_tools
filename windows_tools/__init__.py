#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools package

"""
windows_tools is a meta package for various windows related functions

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'windows_tools'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2018-2021 Orsiris de Jong'
__description__ = 'Toolset for antivirus, NTFS/ReFS ACLs, file ownership, registry, user handling...Well a lot of stuff'
__licence__ = 'BSD 3 Clause'
__version__ = '2.2.0'
__build__ = '2021100401'


# Make sure we declare this file as namespace holder
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
