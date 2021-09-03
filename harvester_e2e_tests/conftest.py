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
        '--rancher-endpoint',
        action='store',
        default=config_data['rancher-endpoint'],
        help='Rancher API endpoint'
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

    # TODO(gyee): may need to add SSL options later


def pytest_configure(config):
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


def pytest_collection_modifyitems(config, items):
    if config.getoption('--vlan-id') != -1:
        # --vlan-id is correctly specified, do not skip tests relying
        # on external routing
        return
    skip_public_network = pytest.mark.skip(reason=(
        'VM not accessible because no VLAN setup with public routing'))
    for item in items:
        if 'public_network' in item.keywords:
            item.add_marker(skip_public_network)
