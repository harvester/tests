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


def pytest_addoption(parser):
    parser.addoption(
        '--endpoint',
        action='store',
        default='https://localhost:30443',
        help='Harvester API endpoint'
    )
    parser.addoption(
        '--username',
        action='store',
        default='admin',
        help='Harvester username'
    )
    parser.addoption(
        '--password',
        action='store',
        default='password',
        help='Harvester password'
    )
    parser.addoption(
        '--do-not-cleanup',
        action='store_true',
        help='Do not cleanup the test artifacts'
    )
    parser.addoption(
        '--harvester_cluster_nodes',
        action='store',
        type='int',
        help='Set count of test framework harvester cluster nodes.'
    )
    parser.addoption(
        '--vlan-id',
        action='store',
        type='int',
        help=('VLAN ID, if specified, will invoke the tests depended on '
              'external networking.')
    )
    parser.addoption(
        '--vlan-nic',
        action='store',
        default='eth0',
        help='Physical NIC for VLAN. Default is "eth0"'
    )
    parser.addoption(
        '--wait-timeout',
        action='store',
        type='int',
        default=300,
        help='Wait time for polling operations'
    )
    parser.addoption(
        '--rancher-endpoint',
        action='store',
        help='Rancher API endpoint'
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


def pytest_collection_modifyitems(config, items):
    if config.getoption('--vlan-id'):
        # --vlan-id is specified, do not skip tests relying on external
        # routing
        return
    skip_public_network = pytest.mark.skip(reason=(
        'VM not accessible because no VLAN setup with public routing'))
    for item in items:
        if 'public_network' in item.keywords:
            item.add_marker(skip_public_network)
