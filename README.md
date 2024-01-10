# windows_tools
## Collection of useful python functions around Microsoft Windows

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Percentage of issues still open](http://isitmaintained.com/badge/open/netinvent/windows_tools.svg)](http://isitmaintained.com/project/netinvent/ofunctions "Percentage of issues still open")
[![Maintainability](https://api.codeclimate.com/v1/badges/0d9732260019ec390649/maintainability)](https://codeclimate.com/github/netinvent/windows_tools/maintainability)
[![codecov](https://codecov.io/gh/netinvent/windows_tools/branch/master/graph/badge.svg?token=6Z03XTQU8G)](https://codecov.io/gh/netinvent/windows_tools)
[![windows-tests](https://github.com/netinvent/windows_tools/actions/workflows/windows.yaml/badge.svg)](https://github.com/netinvent/windows_tools/actions/workflows/windows.yaml)
[![GitHub Release](https://img.shields.io/github/release/netinvent/windows_tools.svg?label=Latest)](https://github.com/netinvent/windows_tools/releases/latest)


windows_tools is a set of various recurrent functions amongst

- antivirus: antivirus state and list of installed AV engines
- bitlocker: drive encryption status and protector key retrieval
- bitness: simple bitness identification
- file_utils: file ownership handling, NTFS & ReFS ACL handling, file listing with permission fixes
- impersonate: python Runas implementation
- installed_software: list of installed software from registry, 32 and 64 bits
- logical_disk: logical disk listing
- misc: basic time related functions to convert windows ticks into epoch / date strings
- office: microsoft Office version identification, works for click & run, O365 and legacy
- powershell: powershell wrapper to identify interpreter and run scripts or commands
- product_key: windows product key retrieval
- registry: registry 32 and 64 bit API
- securityprivilege: enable / disable various security privileges for user
- server: windows server identification
- signtool: Easily sign executables with Authenticode
- updates: get all installed windows updates based on COM, WMI and registry retrieval methods
- users: user lookup for SID/PySID/username
- virtualization: virtualization platform identification for guest
- windows_firewall: windows firewall state retrieval
- wmi_queries: windows WMI query wrapper, wmi timezone converters

It is compatible with Python 3.5+ and is tested on Windows only (obviously).

## Setup

You may install the whole `windows_tools` package or any subpackage using the following commands
```
pip install windows_tools
pip install windows_tools.<subpackage>

```

## Usage

### antivirus

The antivirus package tries to list installed Antivirus products via the SecurityCenter API (using WMI calls).
Since SecurityCenter API does not exist on Windows Servers, we also need to check for installed antivirus software using the uninstall registry keys.
These checks are more fuzzy, but allow to detect the following products:

- avast
- avira
- avg technologies
- bitdefender
- dr web
- eset
- f-secure
- g data software
- kaspersky
- mcafee
- panda security
- sophos
- trend micro
- malwarebytes
- vipre
- sentinel one
- cybereason

On top of that list, it will detect any installed software containing "antivirus/antiviral/antimalware" in the name.

Please report back if your antivirus is not detected, so we can improve the fuzzy detection here.

Usage
```
import windows_tools.antivirus

result = windows_tools.antivirus.get_installed_antivirus_software()
```

`result` will contain a list of dict like

```
[{
        'name': 'Windows Defender',
        'version': None,
        'publisher': None,
        'enabled': False,
        'is_up_to_date': True,
        'type': 'Windows Defender / Security Essentials'
    }, {
        'name': 'Malwarebytes version 4.4.6.132',
        'version': '4.4.6.132',
        'publisher': 'Malwarebytes',
        'enabled': None,
        'is_up_to_date': None,
        'type': None
    }
]
```

**Warning**
Keys `enabled`, `is_up_to_date` and `type` are only filled via securityCenter API*.
Keys `version` and `publisher` are only filled via installed software list.
The only guaranteed filled key will always be `name`

### bitlocker

Bitlocker can only work on NTFS or ReFS formatted disks.
Bitlocker keys can only be retrieved on local disks.

#### Usage

```
import windows_tools.bitlocker

result = windows_tools.bitlocker.get_bitlocker_full_status()
```

`result` will contain a dict as follows containing raw strings from `manage-bde` windows tool:

```
{
	'C:': {
		'status': 'Chiffrement de lecteur BitLocker\xa0: outil de configuration version 10.0.19041\nCopyright (C) 2013 Microsoft Corporation. Tous droits réservés.\n\nVolume C: [Windows ]\n[Volume du système d?exploitation]\n\n    Taille :                     855,14 Go\n    Version de BitLocker :       Aucun\n    État de la conversion :      Intégralement déchiffré\n    Pourcentage chiffré :        0,0%\n    Méthode de chiffrement :     Aucun\n    État de la protection\xa0:      Protection désactivée\n    État du verrouillage :       Déverrouillé\n    Champ d?identification :     Aucun\n    Protecteurs de clés :        Aucun trouvé\n\n', 
		'protectors': None
	},
	'D:': {
		'status': 'Chiffrement de lecteur BitLocker\xa0: outil de configuration version 10.0.19041\nCopyright (C) 2013 Microsoft Corporation. Tous droits réservés.\n\nVolume D: [Étiquette inconnue]\n[Volume de données]\n\n    Taille :                     Inconnu Go\n    Version de BitLocker :       2.0\n    État de la conversion :      Inconnu\n    Pourcentage chiffré :        Inconnu%\n    Méthode de chiffrement :     XTS-AES 128\n    État de la protection\xa0:      Inconnu\n    État du verrouillage :       Verrouillé\n    Champ d?identification :     Inconnu\n    Déverrouillage automatique : Désactivé\n    Protecteurs de clés\xa0:\n        Password\n        Mot de passe numérique\n\n',
		'protectors': 'Chiffrement de lecteur BitLocker\xa0: outil de configuration version 10.0.19041\nCopyright (C) 2013 Microsoft Corporation. Tous droits réservés.\n\nVolume D: [Étiquette inconnue]\nTous les protecteurs de clés\n\n    Password :\n      ID : {SOMEPASS-WORD-ICAN-NNOT-REMEMBERWELL}\n\n    Mot de passe numérique :\n      ID : {SOMEPASS-GUID-ICAN-NNOT-REMEMBERWELL}\n\n'
	}
}
```

You may parse those or simply pretty print since print will not interpret special characters from a dict or multiple variables at once:

```
result = windows_tools.bitlocker.get_bitlocker_full_status()


result = get_bitlocker_full_status()
for drive in result:
    for designation, content in result[drive].items():
        print(designation, content)

```

**Warning** bitlocker needs to be run as admin.
Running as non administrator will produce the following logs

```
Don't have permission to get bitlocker drive status for C:.
Don't have permission to get bitlocker drive protectors for C:.
Don't have permission to get bitlocker drive status for D:.
Don't have permission to get bitlocker drive protectors for D:.
```

Output shall be
```
{
    'C:': {
        'status': None,
        'protectors': None
    },
    'D:': {
        'status': None,
        'protectors': None
    }
}
```

You can check that you have administrator rights with `windows_utils.users` module


### bitness

### file_utils

### impersonate

### installed_software

### logical_disk

### misc

### office

### powershell

### product_key

### registry

### securityprivilege

### server

### signtool

signtool is designed to make the windows executable signature as simple as possible.  
Once the Windows SDK is installed on your machine, you can sign any executable with the following commands:

```
from windows_tools.signtool import SignTool
signer = SignTool()
signer.sign(r"c:\path\to\executable", bitness=64)
```

Note that current versions of `signtool.exe` that come with Windows 10 SDK automagically detect hardware EV certificate tokens like Safenet.

When using former certificate files in order to sign an executable, one should use the following syntax:

```
from windows_tools.signtool import SignTool
signer = SignTool(certificate=r"c:\path\to\cert.pfx", pkcs12_password="the_certificate_file_password")
signer.sign(r"c:\path\to\executable", bitness=64)
```

If the wrong certificate is used to sign, please open `certmgr.msc`, go to Private > Certificates and remove the certificate you don't want.


### updates

Windows updates can be retrieved via a COM object that talks to Windows Update service, via WMI requests or via registry entries.
All methods can return different results, so they are combined into one function.

Usage
```
import windows_tools.updates

result = windows_tools.updates.get_windows_updates(filter_duplicates=True, include_all_states=False)
```

`result` will contain a list of dict like

```
[{
        'kb': 'KB123456',
        'date': '2021-01-01 00:01:02',
        'title': 'Some update title',
        'description': 'Some update description',
        'supporturl': 'https://support.microsoft.com/someID',
        'operation': 'Installation'
        'result': 'Installed'
    }, {
        'kb': None,
        'date': '2021-01-01 00:01:02',
        'title': 'Windows 10 20H1 update',
        'description': 'Pretty big system update',
        'supporturl': 'https://support.microsoft.com/someID',
        'operation': 'Installation'
        'result': 'Installed'
    }
]
```

Using `filter_duplicates` will avoid returning multiple times the same KB from different sources.
This setting is enabled by default.

The parameter `include_all_states` set to True will include all updates, even those who failed to install or are superseeded.

### users

### virtualization

### windows_firewall

### wmi_queries