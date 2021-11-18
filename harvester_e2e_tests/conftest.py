# Copyright (c) 2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

import pytest
import yaml


def pytest_addoption(parser):
    with open('config.yml') as f:
        config_data = yaml.safe_load(f)
    parser.addoption(
        '--endpoint',
        action='store',
        default=config_data['endpoint'],
        help='Harvester API endpoint'
    )
    parser.addoption(
        '--username',
        action='store',
        default=config_data['username'],
        help='Harvester username'
    )
    parser.addoption(
        '--old-password',
        action='store',
        default=config_data['old-password'],
        help='Harvester old admin password'
    )
    parser.addoption(
        '--password',
        action='store',
        default=config_data['password'],
        help='Harvester new admin password'
    )
    parser.addoption(
        '--do-not-cleanup',
        action='store_true',
        default=config_data['do-not-cleanup'],
        help='Do not cleanup the test artifacts'
    )
    parser.addoption(
        '--harvester_cluster_nodes',
        action='store',
        type='int',
        default=config_data['harvester_cluster_nodes'],
        help='Set count of test framework harvester cluster nodes.'
    )
    parser.addoption(
        '--vlan-id',
        action='store',
        type='int',
        default=config_data['vlan-id'],
        help=('VLAN ID, if specified, will invoke the tests depended on '
              'external networking.')
    )
    parser.addoption(
        '--vlan-nic',
        action='store',
        default=config_data['vlan-nic'],
        help='Physical NIC for VLAN. Default is "eth0"'
    )
    parser.addoption(
        '--wait-timeout',
        action='store',
        type='int',
        default=config_data['wait-timeout'],
        help='Wait time for polling operations'
    )
    parser.addoption(
        '--node-scripts-location',
        action='store',
        default=config_data['node-scripts-location'],
        help=('External scripts to power-off, power-up, and reboot a given '
              'Harvester node to facilitate the host-specific tests')
    )
    parser.addoption(
        '--win-image-url',
        action='store',
        default=config_data['win-image-url'],
        help=('Windows image URL ')
    )
    parser.addoption(
        '--terraform-scripts-location',
        action='store',
        default=config_data['terraform-scripts-location'],
        help=('External scripts to create resources using terraform')
    )
    parser.addoption(
        '--backup-scripts-location',
        action='store',
        default=config_data['backup-scripts-location'],
        help=('scripts to create files inside a VM')
    )
    parser.addoption(
        '--image-cache-url',
        action='store',
        default=config_data['image-cache-url'],
        help=('URL for the local images cache')
    )
    parser.addoption(
        '--workaround-restartvm',
        action='store_true',
        default=config_data['workaround-restartvm'],
        help=('when enabled reboot the VM as a workaound for '
              'https://github.com/harvester/harvester/issues/1059')
    )
    parser.addoption(
        '--accessKeyId',
        action='store',
        default=config_data['accessKeyId'],
        help=('A user-id that uniquely identifies your account. ')
    )
    parser.addoption(
        '--secretAccessKey',
        action='store',
        default=config_data['secretAccessKey'],
        help=('The password to your account')
    )
    parser.addoption(
        '--bucketName',
        action='store',
        default=config_data['bucketName'],
        help=('Name of the bucket')
    )
    parser.addoption(
        '--region',
        action='store',
        default=config_data['region'],
        help=('Region of the bucket')
    )
    parser.addoption(
        '--nfs-endpoint',
        action='store',
        default=config_data['nfs-endpoint'],
        help=('Endpoint for storing backup in nfs share')
    )

    # TODO(gyee): may need to add SSL options later


def pytest_configure(config):
    config.addinivalue_line(
        "markers", ('p1: mark test to run only p1 tests ')
    )
    config.addinivalue_line(
        "markers", ('p2: mark test to run only p2 tests ')
    )
    config.addinivalue_line(
        "markers", ('public_network: mark test to run only if public '
                    'networking is available')
    )
    config.addinivalue_line(
        "markers", ('multi_node_scheduling: mark test to run only if we have '
                    'a multi-node cluster where some hosts have more '
                    'resources then others in order to test VM scheduling '
                    'behavior')
    )
    config.addinivalue_line(
        "markers", ('host_management: mark test to run only if we have '
                    'host management (power_on.sh, power_off.sh, reboot.sh) '
                    'scripts provided. These tests are designed to test '
                    'scheduling resiliency and disaster recovery scenarios. ')
    )
    config.addinivalue_line(
        "markers", ('delete_host: mark test to run in the end when other '
                    'tests finished running')
    )
    config.addinivalue_line(
        "markers", ('terraform: mark test to run only if we have terraform.sh '
                    'and terraform provider scripts provided')
    )
    config.addinivalue_line(
        "markers", ('backupnfs: mark test to run only the backup and restore'
                    'tests for NFS backup target')
    )
    config.addinivalue_line(
        "markers", ('backups3: mark test to run only the backup and restore'
                    'tests for S3 backup target')
    )
    config.addinivalue_line(
        "markers", ('imageupload: marker to run imageupload test')
    )
    config.addinivalue_line(
        "markers", ('singlevmtest: marker to run create single vm test')
    )
    config.addinivalue_line(
        "markers", ('multivmtest: marker to run create multiple vms test')
    )
    config.addinivalue_line(
        "markers", ('windows_vm: marker to run only create vm test '
                    'using windows images')
    )
    config.addinivalue_line(
        "markers", ('usbvmtest: marker to run only create vm test with usb')
    )
    config.addinivalue_line(
        "markers", ('nouserdata: marker to run only create vm test '
                    'with nouserdata')
    )
    config.addinivalue_line(
        "markers", ('images_p1: mark test to run only to execute the P1 test '
                    'for images')
    )
    config.addinivalue_line(
        "markers", ('images_p2: mark test to run only to execute the P2 test '
                    'for images')
    )
    config.addinivalue_line(
        "markers", ('terraform_provider_p1: mark test to run only to execute '
                    'the P1 test for terraform provider')
    )
    config.addinivalue_line(
        "markers", ('imageupload: mark test to run upload image')
    )
    config.addinivalue_line(
        "markers", ('volumes_p1: mark test to run only P1 test for Volume')
    )
    config.addinivalue_line(
        "markers", ('volumes_p2: mark test to run only P2 test for Volume')
    )
    config.addinivalue_line(
        "markers", ('authentication_p1: mark test to run only P1 '
                    'test for authentication')
    )
    config.addinivalue_line(
        "markers", ('hosts_p1: mark test to run only P1 test for Hosts')
    )
    config.addinivalue_line(
        "markers", ('hosts_p2: mark test to run only P1 test for Hosts')
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption('--vlan-id') == -1:
        skip_public_network = pytest.mark.skip(reason=(
            'VM not accessible because no VLAN setup with public routing'))
        for item in items:
            if 'public_network' in item.keywords:
                item.add_marker(skip_public_network)

    if config.getoption('--win-image-url') == '':
        skip_windows_vm = pytest.mark.skip(reason=(
            'Windows image not specified'))
        for item in items:
            if 'windows_vm' in item.keywords:
                item.add_marker(skip_windows_vm)

    if (config.getoption('--nfs-endpoint') == '' and
            config.getoption('--accessKeyId') == ''):
        skip_backup = pytest.mark.skip(reason=(
            'AWS credentials or NFS endpoint are not available'))
        for item in items:
            if 'backup' in item.keywords:
                item.add_marker(skip_backup)

    if config.getoption('--accessKeyId') == '':
        skip_backup = pytest.mark.skip(reason=(
            'AWS credentials are not available'))
        for item in items:
            if 'backups3' in item.keywords:
                item.add_marker(skip_backup)

    if config.getoption('--nfs-endpoint') == '':
        skip_backup = pytest.mark.skip(reason=(
            'NFS endpoint is not available'))
        for item in items:
            if 'backupnfs' in item.keywords:
                item.add_marker(skip_backup)
