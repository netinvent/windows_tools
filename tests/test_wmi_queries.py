#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of command_runner module

"""
wmi_queries wrapper
transforms wmi objects into python dicts
Handles most runtime errors


Versioning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'tests.windows_tools.wmi_queries'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020-2021 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__build__ = '2021021601'

from windows_tools.wmi_queries import *

CIM_TIMESTAMP_REGEX = r'[0-9]{4}[0-1][0-9][0-3][0-9][0-1][0-9]([0-5][0-9]){2}\.[0-9]{5,6}(\+|-)[0-9]{2,3}'


def test_wmi_object_2_list_of_dict():
    print('Testing WMI object conversion')
    raw_result = wmi.WMI(namespace='cimv2').Win32_LoggedOnUser()
    assert isinstance(raw_result[0], wmi._wmi_object), 'Raw result should be a WMI object'
    result = wmi_object_2_list_of_dict(raw_result)
    assert isinstance(result[0], dict), 'Converted result should be a dict'
    try:
        assert result[0]['Antecedent']['AccountType'] is not None, 'Should not exist here'
    except TypeError:
        pass
    else:
        assert False, 'First conversion should not have a depth more than 1'
    two_depth_result = wmi_object_2_list_of_dict(raw_result, depth=2)
    # SID should exist regardless of the user account we're making the wmi request with
    assert two_depth_result[0]['Antecedent']['SID'] is not None, 'Two depth result should have AccountType'


def test_query_wmi():
    """
    May fail on elder OS without bitlocker Win32_EncyptableVolume class
    """
    print('Testing WMI query Operating system')
    result = query_wmi('SELECT * FROM Win32_OperatingSystem', 'cimv2', 'test_query', can_be_skipped=False)
    assert result[0]['Status'] == 'OK', 'WMI Query for Win32_OperatingSystem: status != OK'

    print('Testing WMI query EncryptableVolume')
    result = query_wmi('SELECT * FROM Win32_EncryptableVolume', 'cimv2/Security/MicrosoftVolumeEncryption', 'test')
    assert isinstance(result[0]['ConversionStatus'], int), 'Bitlocker query should give a conversionStatus, ' \
                                                           'do we run as admin ?'


def test_get_wmi_timezone_bias():
    """
    bias is what Microsoft calls the minute difference (signed) from UTC time
    """
    bias = int(get_wmi_timezone_bias())
    print('Current timzeone bias: ', bias)
    assert -(23 * 60) < bias < (23 * 60), 'Timezone bias should be in -23 hours up to +23 hours'


def test_cim_timestamp_to_datetime():
    print('Testing cim timestamp to datetime object')

    cim_ts = '20201103225935.123456+0'
    dt = cim_timestamp_to_datetime_utc(cim_ts)
    assert isinstance(dt, datetime) is True, 'Timestamp null TZ conversion failed'
    assert dt.timestamp() == 1604444375.123456, 'cim timestamp to timestamp conversion failed'

    cim_ts = '20201103225935.123456-240'
    dt = cim_timestamp_to_datetime_utc(cim_ts)
    assert isinstance(dt, datetime) is True, 'Timestamp with negative TZ conversion failed'
    assert dt.timestamp() == 1604429975.123456, 'cim timestamp to timestamp conversion failed'

    cim_ts = '20201103225935.123456+240'
    dt = cim_timestamp_to_datetime_utc(cim_ts)
    assert isinstance(dt, datetime) is True, 'Timestamp with negative TZ conversion failed'
    assert dt.timestamp() == 1604458775.123456, 'cim timestamp to timestamp conversion failed'


def test_datetime_to_cim_timestamp():
    print('Test datetime to cim timestamp')

    dt = datetime(2021, 2, 17, 11, 35, 31, 228381)
    cim_timestamp = datetime_to_cim_timestamp(dt)
    assert re.match(CIM_TIMESTAMP_REGEX, cim_timestamp), 'Bogus cim timestamp'
    assert '20210217113531.228381' in cim_timestamp, 'Cim timestamp has wrong date'


def test_create_current_cim_timestamp():
    print('Test create current cim timestamp')

    cim_ts = create_current_cim_timestamp(hour_offset=0)
    curr_dt = datetime.utcnow()
    dt = cim_timestamp_to_datetime_utc(cim_ts)
    assert isinstance(dt, datetime) is True, 'cim timestamp creation failed failed'
    assert dt.year == curr_dt.year, 'cim timestamp creation failed failed'
    assert dt.month == curr_dt.month, 'cim timestamp creation failed failed'
    assert dt.day == curr_dt.day, 'cim timestamp creation failed failed'
    assert dt.hour == curr_dt.hour, 'cim timestamp creation failed failed'
    # Too precise, will fail often
    # Can still fail when cim_ts is computed at the last second of an hour
    # assert dt.minute == curr_dt.minute, 'cim timestamp creation failed failed'
    # assert dt.second == curr_dt.second, 'cim timestamp creation failed failed'

    cim_ts = create_current_cim_timestamp(hour_offset=3)
    curr_dt = datetime.utcnow()
    dt = cim_timestamp_to_datetime_utc(cim_ts)
    assert isinstance(dt, datetime) is True, 'cim timestamp creation failed failed'
    assert dt.year == curr_dt.year, 'cim timestamp creation failed failed'
    assert dt.month == curr_dt.month, 'cim timestamp creation failed failed'
    assert dt.day == curr_dt.day, 'cim timestamp creation failed failed'
    assert dt.hour + 3 == curr_dt.hour, 'cim timestamp creation failed failed'
    # Too precise, will fail often
    # Can still fail when cim_ts is computed at the last second of an hour
    # assert dt.minute == curr_dt.minute, 'cim timestamp creation failed failed'
    # assert dt.second == curr_dt.second, 'cim timestamp creation failed failed'


if __name__ == '__main__':
    print('Example code for %s, %s' % (__intname__, __build__))
    test_wmi_object_2_list_of_dict()
    test_query_wmi()
    test_get_wmi_timezone_bias()
    test_cim_timestamp_to_datetime()
    test_datetime_to_cim_timestamp()
    test_create_current_cim_timestamp()
