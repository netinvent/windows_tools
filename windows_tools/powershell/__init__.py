#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of windows_tools module

"""
PowerShellRunner is a class that allows to run powershell scripts / commands without hassle
Also allows auto script elevation

Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = "windows_tools.powershell"
__author__ = "Orsiris de Jong"
__copyright__ = "Copyright (C) 2019-2026 Orsiris de Jong"
__description__ = "PowerShell interpreter wrapper"
__licence__ = "BSD 3 Clause"
__version__ = "0.6.0"
__build__ = "2026032701"

import os
from logging import getLogger
import tempfile

from command_runner import command_runner
from ofunctions.json_sanitize import json_sanitize
from ofunctions.random import random_string
import windows_tools.registry

logger = getLogger()


def _powershell_elevator_script(hidden=False):
    """
    Returns a wrapper script for powershell commands / scripts
    that will try elevation and get stdout/stderr and exit code (0 or 1) of the elevated process
    """
    script = r"""
    # Run elevated commands and get stdout/stderr and (partial) exitcode

    try {
        # Function blatantly stolen from https://stackoverflow.com/a/15669365/2635443
        function Write-StdErr {
            param ([PSObject] $InputObject)
            $outFunc = if ($Host.Name -eq 'ConsoleHost') {
                [Console]::Error.WriteLine
            } else {
            $host.ui.WriteErrorLine
            }
            if ($InputObject) {
                [void] $outFunc.Invoke($InputObject.ToString())
            } else {
                [string[]] $lines = @()
                $Input | % { $lines += $_.ToString() }
                [void] $outFunc.Invoke($lines -join "`r`n")
            }
        }

        # Parts blatanly stolen from https://stackoverflow.com/a/60216595/2635443

        # Get the ID and security principal of the current user account
        $myWindowsID=[System.Security.Principal.WindowsIdentity]::GetCurrent()
        $myWindowsPrincipal=new-object System.Security.Principal.WindowsPrincipal($myWindowsID)

        # Get the security principal for the Administrator role
        $adminRole=[System.Security.Principal.WindowsBuiltInRole]::Administrator

        # Check to see if we are currently running "as Administrator"
        if ($myWindowsPrincipal.IsInRole($adminRole))
            {
                #Update window to show we're running as administrator
                $Host.UI.RawUI.WindowTitle = $myInvocation.MyCommand.Definition + "(Elevated)"
                $Host.UI.RawUI.BackgroundColor = "DarkBlue"
                clear-host
                $Host.UI.Write("Running elevated NPBackup task processing")
            } else {
                $capture_stdout = New-TemporaryFile
                $capture_stderr = New-TemporaryFile
                # Relaunch our processs as admin
                # This will disconnect fds, so we need to redirect stdout and stderr in order to catch them
                $processParams = new-object System.Diagnostics.ProcessStartInfo "PowerShell";

                # Specify the current script path and name as a parameter
                $processParams.Arguments = $myInvocation.MyCommand.Definition;
                $processParams.Arguments += " > $capture_stdout 2> $capture_stderr"

                # Indicate that the process should be elevated
                $processParams.Verb = "RunAs"
                # We might hide our window, or leave this commented out so options above apply
                ___HIDDEN_PLACEHOLDER___

                # Start the new process
                try {
                    $process = [System.Diagnostics.Process]::Start($processParams)
                    While (-not $process.HasExited) {
                        Start-Sleep -Milliseconds 100
                    }
                    # Arbitrary wait time for fds to close
                    Start-Sleep -Milliseconds 500
                    Write-Host (Get-Content -Path $capture_stdout)
                    Write-StdErr (Get-Content -Path $capture_stderr)
                    # This will only return 0 or 1, other integers are transformed into 1
                    exit($process.ExitCode)
                } catch {
                    Write-output "Process cannot be launched as admin. Trying as standard user"
                }
            
            }

        # The following code will run elevated
        ___CODE_PLACEHOLDER___
    } catch {
        Write-Host "PS Error: $($_.Exception.Message)"*
        exit(1)
    }
    """
    if hidden:
        script = script.replace(
            "___HIDDEN_PLACEHOLDER___", '$processParams.WindowStyle = "Hidden"'
        )
    else:
        script = script.replace("___HIDDEN_PLACEHOLDER___", "")
    return script


class PowerShellRunner:
    """
    Identify powershell interpreter and allow running scripts / commands with ExecutionPolicy ByPass
    """

    def __init__(self, powershell_interpreter=None):
        self._interactive = False
        self._tmp_script_identifier = __intname__

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

    @property
    def interactive(self):
        return self._interactive

    @interactive.setter
    def interactive(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("Interactive property must be a boolean")
        self._interactive = value

    @property
    def tmp_script_identifier(self):
        return self._tmp_script_identifier

    @tmp_script_identifier.setter
    def tmp_script_identifier(self, value):
        if not isinstance(value, str):
            raise ValueError("_tmp_script_identifier property must be a string")
        self._tmp_script_identifier = value

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
        **kwargs,
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
        command = self.powershell_interpreter + "{} -NoLogo {}{}{}".format(
            " -NonInteractive" if not self.interactive else "",
            utf8_prefix,
            command,
            to_json_suffix,
        )
        logger.debug("Running powershell command:\n%s", command)

        exit_code, output = command_runner(
            command,
            timeout=timeout,
            valid_exit_codes=valid_exit_codes,
            encoding=encoding,
            **kwargs,
        )
        if sanitize_json:
            return exit_code, json_sanitize(output)
        return exit_code, output

    def run_script(
        self,
        script,
        *args,
        timeout=None,
        valid_exit_codes=[0],
        encoding=None,
        elevated=False,
        **kwargs,
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

        if elevated:
            try:
                # We need to prepare a temporary script that will be injected into the elevator script
                if script.endswith(".ps1") and os.path.isfile(script):
                    with open(script, "r", encoding=encoding) as fp:
                        script_content = fp.read()
                    powershell_elevator_script = _powershell_elevator_script(
                        hidden=not self.interactive
                    ).replace("___CODE_PLACEHOLDER___", script_content)
                else:
                    # Assume we are given an inline script instead of a file
                    powershell_elevator_script = _powershell_elevator_script(
                        hidden=not self.interactive
                    ).replace("___CODE_PLACEHOLDER___", script)

                # Write a temporary elevator script with the content of the given script
                powershell_elevator_temp_script = os.path.join(
                    tempfile.gettempdir(),
                    "{}_{}.ps1".format(self._tmp_script_identifier, random_string(8)),
                )
                with open(
                    powershell_elevator_temp_script, "w", encoding=encoding
                ) as fp:
                    fp.write(powershell_elevator_script)
                script = powershell_elevator_temp_script
            except OSError as exc:
                logger.error("Could not prepare powershell elevator: {}".format(exc))
                return 1, "Could not prepare powershell elevator: {}".format(exc)

        # Welcome in Powershell hell where running a script with -Command argument returns exit
        # codes 0 or 1 whereas as running with -File argument returns your script exit code
        command = (
            self.powershell_interpreter
            + ' -executionPolicy Bypass{} -NoLogo -NoProfile -File "{}"'.format(
                " -NonInteractive" if not self.interactive else "", script
            )
            + (" " if len(args) > 0 else " ")
            + " ".join('"' + arg + '"' for arg in args)
        )
        logger.debug("Running powershell command:\n%s", command)
        exit_code, output = command_runner(
            command,
            timeout=timeout,
            valid_exit_codes=valid_exit_codes,
            encoding=encoding,
            **kwargs,
        )
        try:
            os.remove(powershell_elevator_temp_script)
        except Exception as exc:
            logger.debug(
                "Could not remove temporary powershell elevator script: {}".format(exc)
            )
        return exit_code, output
