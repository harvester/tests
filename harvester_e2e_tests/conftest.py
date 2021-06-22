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


def pytest_addoption(parser):
    parser.addoption(
        '--endpoint',
        action='store',
        default='https://localhost:8443',
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
    # TODO(gyee): may need to add SSL options later
