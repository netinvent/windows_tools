# windows_tools
## Collection of useful python functions around Microsoft Windows

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Percentage of issues still open](http://isitmaintained.com/badge/open/netinvent/windows_tools.svg)](http://isitmaintained.com/project/netinvent/ofunctions "Percentage of issues still open")

windows_tools is a set of various recurrent functions amongst

- antivirus: antivirus state and list of installed AV engines
- bitlocker: drive encryption status and protector key retrieval
- bitness: simple bitness identification
- file_utils: file ownership handling, NTFS & ReFS ACL handling, file listing with permission fixes
- impersonate: python Runas implementation
- installed_software: list of installed software from registry, 32 and 64 bits
- logical_disk: logical disk listing
- office: microsoft Office version identification, works for click & run, O365 and legacy
- powershell: powershell wrapper to identify interpreter and run scripts or commands
- product_key: windows product key retrieval
- registry: registry 32 and 64 bit API
- securityprivilege: enable / disable various security privileges for user
- server: windows server identifivation
- users: user lookup for SID/PySID/username
- virtualization: virtualization platform identification for guest
- windows_firewall: windows firewall state retrieval
- wmi_queries: windows WMI query wrapper, wmi timezone converters

## Setup

```
pip install windows_tools.<subpackage>

```
