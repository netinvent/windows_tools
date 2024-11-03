#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
PowerShellRunner is a class that allows to run powershell scripts / commands without hassle

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "windows_tools.powershell"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2019-2024 Orsiris de Jong"
__description__ = "PowerShell interpreter wrapper"
__licence__ = "BSD 3 Clause"
__version__ = "0.4.0"
__build__ = "2024102301"

import os
from logging import getLogger

from command_runner import command_runner
from ofunctions.json_sanitize import json_sanitize
import windows_tools.registry


logger = getLogger()


class PowerShellRunner:
    """
    Identify powershell interpreter and allow running scripts / commands with ExecutionPolicy ByPass
    """

    def __init__(self, powershell_interpreter=None):
        self.powershell_interpreter = powershell_interpreter

        if powershell_interpreter is not None and os.path.isfile(
            powershell_interpreter
        ):
            return

        # Try to guess powershell path if no valid path given
        interpreter_executable = "powershell.exe"
        for syspath in ["sysnative", "system32"]:
            try:
                # Let's try native powershell (64 bit) first or else
                # Import-Module may fail when running 32 bit powershell on 64 bit arch
                best_guess = os.path.join(
                    os.environ.get("SYSTEMROOT", "C:"),
                    syspath,
                    "WindowsPowerShell",
                    "v1.0",
                    interpreter_executable,
                )
                if os.path.isfile(best_guess):
                    self.powershell_interpreter = best_guess
                    break
            except KeyError:
                pass
        if self.powershell_interpreter is None:
            try:
                ps_paths = os.path.dirname(os.environ["PSModulePath"]).split(";")
                for ps_path in ps_paths:
                    if ps_path.endswith("Modules"):
                        ps_path = ps_path.strip("Modules")
                    possible_ps_path = os.path.join(ps_path, interpreter_executable)
                    if os.path.isfile(possible_ps_path):
                        self.powershell_interpreter = possible_ps_path
                        break
            except KeyError:
                pass

        if self.powershell_interpreter is None:
            raise OSError("Could not find any valid powershell interpreter")

        self.major_version = None
        self.minor_version = None
        self.major_version, self.minor_version = self.get_version()

    def get_version(self):
        """
        Get major / minor version as tuple

        """
        if self.powershell_interpreter is None:
            return 0, 0

        try:
            exit_code, output = self.run_command("$PSVersionTable.PSVersion.ToString()")
            if exit_code != 0:
                # If the above method does not work, let's try registry method
                try:
                    output = windows_tools.registry.get_value(
                        hive=windows_tools.registry.HKEY_LOCAL_MACHINE,
                        key=r"SOFTWARE\Microsoft\PowerShell\3\PowerShellEngine",
                        value="PowerShellVersion",
                    )
                except FileNotFoundError:
                    output = "-1.-1"
            try:
                # output = major_version.minor_version.build.revision for newer powershells
                major_version, minor_version, _, _ = output.split(".")
            except (ValueError, TypeError):
                # output = major_version.minor_version for some powershells (v3.0)
                major_version, minor_version = output.split(".")
            return int(major_version), int(minor_version)
        except (ValueError, TypeError):
            return -1, 0

    def run_command(
        self,
        command,
        timeout=None,
        valid_exit_codes=[0],
        encoding=None,
        force_utf8=True,
        to_json=False,
        json_depth=2,
        sanitize_json=True,
        **kwargs
    ):
        """
        Accepts subprocess.check_output arguments
        Accepts command_runner arguments like timeout, encoding and valid_exit_codes

        """
        if self.powershell_interpreter is None:
            return False

        # So older powershell versions used unicode_escape, newer ones are utf-8
        # AFAIK, the change happened between powershell 4 and 5
        if not encoding and self.major_version is not None:
            if self.major_version >= 5:
                encoding = "utf-8"
            else:
                encoding = "unicode_escape"

        utf8_prefix = ""
        if force_utf8:
            utf8_prefix = "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        to_json_suffix = ""
        if to_json:
            to_json_suffix = "| ConvertTo-Json -Depth {}".format(json_depth)

        # Do not add -NoProfile so we don't end up in a path we're not supposed to
        command = (
            self.powershell_interpreter
            + " -NonInteractive -NoLogo {}{}{}".format(
                utf8_prefix, command, to_json_suffix
            )
        )
        logger.debug("Running powershell command:\n%s", command)
        exit_code, output = command_runner(
            command,
            timeout=timeout,
            valid_exit_codes=valid_exit_codes,
            encoding=encoding,
            **kwargs
        )
        if sanitize_json:
            return exit_code, json_sanitize(output)
        return exit_code, output

    def run_script(
        self, script, *args, timeout=None, valid_exit_codes=[0], encoding=None, **kwargs
    ):
        """
        Accepts subprocess.check_output arguments
        """

        if self.powershell_interpreter is None:
            return False

        if not encoding and self.major_version is not None:
            if self.major_version >= 5:
                encoding = "utf-8"
            else:
                encoding = "unicode_escape"

        # Welcome in Powershell hell where running a script with -Command argument returns exit
        # codes 0 or 1 whereas as running with -File argument returns your script exit code
        command = (
            self.powershell_interpreter
            + " -executionPolicy Bypass -NonInteractive -NoLogo -NoProfile -File "
            + script
            + (" " if len(args) > 0 else " ")
            + " ".join('"' + arg + '"' for arg in args)
        )
        logger.debug("Running powershell command:\n%s", command)
        exit_code, output = command_runner(
            command,
            timeout=timeout,
            valid_exit_codes=valid_exit_codes,
            encoding=encoding,
            **kwargs
        )
        return exit_code, output
