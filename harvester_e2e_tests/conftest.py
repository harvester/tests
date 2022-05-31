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
        '--password',
        action='store',
        default=config_data['password'],
        help='Harvester password'
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
        type=int,
        default=config_data['harvester_cluster_nodes'],
        help='Set count of test framework harvester cluster nodes.'
    )
    parser.addoption(
        '--vlan-id',
        action='store',
        type=int,
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
        type=int,
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
    parser.addoption(
        '--rancher-version',
        action='store',
        default=config_data['rancher-version'],
        help=('Rancher Docker image version to use when bootstrapping Rancher '
              'VM in Harvester')
    )
    parser.addoption(
        '--rancher-endpoint',
        action='store',
        default=config_data.get('rancher-endpoint', None),
        help='Rancher API endpoint'
    )
    parser.addoption(
        '--rancher-admin-password',
        action='store',
        default=config_data.get('rancher-admin-password', None),
        help='Rancher admin user password'
    )
    parser.addoption(
        '--kubernetes-version',
        action='store',
        default=config_data.get('kubernetes-version', 'v1.21.6+rke2r1'),
        help='Kubernetes version to use for Rancher integration tests'
    )
    parser.addoption(
        '--test-environment',
        action='store',
        default='local',
        help=('QE test environment (e.g. chiefs, raiders, etc), for '
              'distinguishing the test artifacts in the case where an '
              'dependency (e.g. Rancher) is shared amongst the '
              'test environments. If you are running local Vagrant, you '
              'should name the environment to your username (e.g. gyee)')
    )
    parser.addoption(
        '--rancher-cluster-wait-timeout',
        action='store',
        type=int,
        default=config_data['rancher-cluster-wait-timeout'],
        help='Wait time for polling Rancher cluster ready status'
    )
    parser.addoption(
        '--nfs-mount-dir',
        action='store',
        default=config_data['nfs-mount-dir'],
        help=('mount directory for nfs share')
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
        "markers", ('virtual_machines_p1: marker to run only P1 '
                    ' Virtual Machine test')
    )
    config.addinivalue_line(
        "markers", ('virtual_machines_p2: marker to run only P2  '
                    ' Virtual Machine test')
    )
    config.addinivalue_line(
        "markers", ('network_p1: marker to run only P1 Network test ')
    )
    config.addinivalue_line(
        "markers", ('network_p2: marker to run only P2 Network test ')
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
        "markers", ('backup_and_restore_p1: mark test to run only to execute '
                    'the P1 test for Backup and Recovery')
    )
    config.addinivalue_line(
        "markers", ('backup_and_restore_p2: mark test to run only to execute '
                    'the P2 test for Backup and Recovery')
    )
    config.addinivalue_line(
        "markers", ('hosts_p1: mark test to run only P1 test for Hosts')
    )
    config.addinivalue_line(
        "markers", ('hosts_p2: mark test to run only P1 test for Hosts')
    )
    config.addinivalue_line(
        "markers", ('terraform_provider_p1: mark test to run only P1 test '
                    'for terraform provider')
    )
    config.addinivalue_line(
        "markers", ('rancher: mark rancher integration  tests ')
    )
    config.addinivalue_line(
        "markers", (
            'rancher_integration_with_external_rancher: mark Rancher '
            'integration tests with an external Rancher')
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

    if (not config.getoption('--rancher-endpoint') and
            not config.getoption('--rancher-admin-password')):
        skip_rancher_integration_external = pytest.mark.skip(reason=(
            'Rancher endpoint and admin password are not specified'))
        for item in items:
            if 'rancher_integration_with_external_rancher' in item.keywords:
                item.add_marker(skip_rancher_integration_external)
