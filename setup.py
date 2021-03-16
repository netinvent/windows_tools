#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools package


__intname__ = 'windows_tools.setup'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2021 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__build__ = '2021031601'

"""
Namespace packaging here

# Make sure we declare an __init__.py file as namespace holder in the package root containing the following

try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
"""

import sys
import os
import shutil

import pkg_resources
import setuptools


def _read_file(filename):
    here = os.path.abspath(os.path.dirname(__file__))
    if sys.version_info[0] > 2:
        with open(os.path.join(here, filename), 'r', encoding='utf-8') as file_handle:
            return file_handle.read()
    else:
        # With python 2.7, open has no encoding parameter, resulting in TypeError
        # Fix with io.open (slow but works)
        from io import open as io_open
        with io_open(os.path.join(here, filename), 'r', encoding='utf-8') as file_handle:
            return file_handle.read()


def get_metadata(package_file):
    """
    Read metadata from package file
    """

    _metadata = {}

    for line in _read_file(package_file).splitlines():
        if line.startswith('__version__') or line.startswith('__description__'):
            delim = '='
            _metadata[line.split(delim)[0].strip().strip('__')] = line.split(delim)[1].strip().strip('\'"')
    return _metadata


def parse_requirements(filename):
    """
    There is a parse_requirements function in pip but it keeps changing import path
    Let's build a simple one
    """
    try:
        requirements_txt = _read_file(filename)
        install_requires = [
            str(requirement)
            for requirement
            in pkg_resources.parse_requirements(requirements_txt)
        ]
        return install_requires
    except OSError:
        print('WARNING: No requirements.txt file found as "{}". Please check path or create an empty one'
              .format(filename))


def clear_package_build_path(package_rel_path):
    """
    We need to clean build path, but setuptools will wait for build/lib/package_name so we need to create that
    """
    build_path = os.path.abspath(os.path.join('build', 'lib', package_rel_path))
    try:
        # We need to use shutil.rmtree() instead of os.remove() since the latter implementation
        # produces "WindowsError: [Error 5] Access is denied"
        shutil.rmtree('build')
    except FileNotFoundError:
        print('build path: {} does not exist'.format(build_path))
    # Now we need to create the 'build/lib/package/subpackage' path so setuptools won't fail
    os.makedirs(build_path)


#  ######### ACTUAL SCRIPT ENTRY POINT

NAMESPACE_PACKAGE_NAME = 'windows_tools'
namespace_package_path = os.path.abspath(NAMESPACE_PACKAGE_NAME)
namespace_package_file = os.path.join(namespace_package_path, '__init__.py')
metadata = get_metadata(namespace_package_file)
requirements = parse_requirements(os.path.join(namespace_package_path, 'requirements.txt'))
long_description = _read_file('README.md')

# First lets make sure build path is clean (avoiding namespace package pollution in subpackages)
# Clean build dir before every run so we don't make cumulative wheel files
clear_package_build_path(NAMESPACE_PACKAGE_NAME)

# Generic namespace package
setuptools.setup(
    name=NAMESPACE_PACKAGE_NAME,
    namespace_packages=[NAMESPACE_PACKAGE_NAME],
    packages=setuptools.find_namespace_packages(include=['windows_tools.*']),
    version=metadata['version'],
    install_requires=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Topic :: System",
        "Topic :: System :: Operating System",
        "Topic :: System :: Shells",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: Microsoft",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: BSD License",
    ],
    description=metadata['description'],
    license='BSD',
    author='NetInvent - Orsiris de Jong',
    author_email='contact@netinvent.fr',
    url='https://github.com/netinvent/windows_tools',
    keywords=['wmi', 'virtualization', 'file', 'acl', 'ntfs', 'refs', 'antivirus', 'security', 'firewall', 'office'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.5',
    # namespace packages don't work well with zipped eggs
    # ref https://packaging.python.org/guides/packaging-namespace-packages/
    zip_safe=False
)



for package in setuptools.find_namespace_packages(include=['windows_tools.*']):
    rel_package_path = package.replace('.', os.sep)
    package_path = os.path.abspath(rel_package_path)
    package_file = os.path.join(package_path, '__init__.py')
    metadata = get_metadata(package_file)
    requirements = parse_requirements(os.path.join(package_path, 'requirements.txt'))
    print(package_path)
    print(package_file)
    print(metadata)
    print(requirements)

    # Again, we need to clean build paths between runs
    clear_package_build_path(rel_package_path)

    setuptools.setup(
        name=package,
        namespace_packages=[NAMESPACE_PACKAGE_NAME],
        packages=[package],
        package_data={package: ['__init__.py']},
        version=metadata['version'],
        install_requires=requirements,
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Developers",
            "Topic :: Software Development",
            "Topic :: System",
            "Topic :: System :: Operating System",
            "Topic :: System :: Shells",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: Implementation :: CPython",
            "Programming Language :: Python :: Implementation :: PyPy",
            "Operating System :: Microsoft",
            "Operating System :: Microsoft :: Windows",
            "License :: OSI Approved :: BSD License",
        ],
        description=metadata['description'],
        author='NetInvent - Orsiris de Jong',
        author_email='contact@netinvent.fr',
        url='https://github.com/netinvent/windows_tools',
        keywords=['wmi', 'virtualization', 'file', 'acl', 'ntfs', 'refs', 'antivirus', 'security', 'firewall', 'office'],
        long_description=long_description,
        long_description_content_type="text/markdown",
        python_requires='>=3.5',
        # namespace packages don't work well with zipped eggs
        # ref https://packaging.python.org/guides/packaging-namespace-packages/
        zip_safe=False
    )

