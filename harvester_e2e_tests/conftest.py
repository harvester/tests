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
from pytest_dependency import DependencyManager as DepMgr


def check_depends(self, depends, item):
    # monkey patch `DependencyManager.checkDepends`

    marker = item.get_closest_marker("dependency")
    if marker and marker.kwargs.get('param'):
        try:
            param_id = item.callspec.id
            depends = [f"{d}[{param_id}]" for d in depends]
        except AttributeError:
            pass

    # ref: https://github.com/RKrahl/pytest-dependency/issues/57#issuecomment-1000896418
    if marker and marker.kwargs.get('any'):
        for depend in depends:
            try:
                self._check_depend([depend], item)
            except pytest.skip.Exception:
                continue
            else:
                return
        pytest.skip("%s depends on any of %s" % (item.name, ", ".join(depends)))
    else:
        self._check_depend(depends, item)


DepMgr.checkDepend, DepMgr._check_depend = check_depends, DepMgr.checkDepend


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
        '--host-password',
        action='store',
        default=config_data['host-password'],
        help='Password to access Harvesrer node'
    )
    parser.addoption(
        '--host-private-key',
        action='store',
        default=config_data['host-private-key'],
        help='private key to access Harvester node'
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
        '--sleep-timeout',
        action='store',
        type=int,
        default=config_data['sleep-timeout'],
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
        '--opensuse-image-url',
        action='store',
        default=config_data.get('opensuse-image-url'),
        help=('OpenSUSE image URL')
    )
    parser.addoption(
        '--terraform-scripts-location',
        action='store',
        default=config_data['terraform-scripts-location'],
        help=('External scripts to create resources using terraform')
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
        '--s3-endpoint',
        action='store',
        default=config_data.get('s3-endpoint', ''),
        help=('S3 endpoint')
    )
    parser.addoption(
        '--nfs-endpoint',
        action='store',
        default=config_data['nfs-endpoint'],
        help=('Endpoint for storing backup in nfs share')
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
        '--RKE2-version',
        action='store',
        default=config_data.get('RKE2-version'),
        help='RKE2 Kubernetes version to use for Rancher integration tests'
    )
    parser.addoption(
        '--RKE1-version',
        action='store',
        default=config_data.get('RKE1-version'),
        help='RKE1 Kubernetes version to use for Rancher integration tests'
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
    parser.addoption(
        '--upgrade-prepare-dependence',
        action='store',
        default=config_data['upgrade-prepare-dependence'],
        help=('If true to prepare dependence')
    )
    parser.addoption(
        '--upgrade-sc-replicas',
        action='store',
        default=config_data['upgrade-sc-replicas'],
        help=('default storage class replicas')
    )
    parser.addoption(
        '--upgrade-target-version',
        action='store',
        default=config_data['upgrade-target-version'],
        help=('test target harvester version')
    )
    parser.addoption(
        '--upgrade-iso-url',
        action='store',
        default=config_data['upgrade-iso-url'],
        help=('URL for specific iso')
    )
    parser.addoption(
        '--upgrade-iso-checksum',
        action='store',
        default=config_data['upgrade-iso-checksum'],
        help=('URL for specific iso checksum')
    )
    parser.addoption(
        '--upgrade-wait-timeout',
        action='store',
        default=config_data['upgrade-wait-timeout'],
        help=('Wait time for polling upgrade Harvester cluster completed status')
    )
    parser.addoption(
        '--terraform-provider-harvester',
        action='store',
        default=config_data.get('terraform-provider-harvester'),
        help=('Version of Terraform Harvester Provider')
    )


def pytest_configure(config):
    # Register marker as the format (marker, (description))
    markers = [
        ("skip_version_before", (
            "mark test skipped when cluster version < provided version")),
        ("skip_version_after", (
            "mark test skipped when cluster version >= provided version")),
        ('p0', ("mark the test's priority is p0")),
        ('p1', ("mark the test's priority is p1")),
        ('p2', ("mark the test's priority is p2")),
        ('hosts', ('{_r} host tests')),
        ('delete_host', ('{_r} host and will delete one of hosts')),
        ("negative", ("{_r} a negative tests")),
        ('keypairs', ("{_r} SSH keypairs tests")),
        ('images', ("{_r} image tests")),
        ("networks", ("{_r} vlan network tests")),
        ("volumes", ("{_r} volume tests")),
        ("virtualmachines", ("{_r} VM tests")),
        ("templates", ("{_r} VM template tests")),
        ("support_bundle", ("{_r} Support Bundle tests")),
        ("settings", ("{_r} settings tests")),
        ("upgrade", ("{_r} upgrade tests")),
        ("any_nodes", ("{_r} tests which could be ran on clushter with any nodes")),
        ("single_node", ("{_r} tests which could only be ran on cluster with single node")),
        ("three_nodes", ("{_r} tests which could only be ran on cluster with three nodes")),
        ('rancher', ("{_r} rancher integration tests")),
        ('rke1', ("{_r} rancher RKE1 tests")),
        ('rke2', ("{_r} rancher RKE2 tests")),
        ('terraform', ("{_r} terraform tests")),
        ('virtualmachines', ('{_r} virtualmachines tests')),
        ('backup_target', ('{_r} backup-target tests')),
        ('S3', ('{_r} backup-target tests with S3')),
        ('NFS', ('{_r} backup-target tests with NFS'))
    ]

    for m, msg in markers:
        related = 'mark the test is related to'
        config.addinivalue_line("markers", f"{m}:{msg.format(_r=related)}")


@pytest.hookimpl(hookwrapper=True)
def pytest_collection_modifyitems(session, config, items):
    if config.getoption('--vlan-id') == -1:
        skip_public_network = pytest.mark.skip(reason=(
            'VM not accessible because no VLAN setup with public routing'))
        for item in items:
            if 'public_network' in item.keywords:
                item.add_marker(skip_public_network)

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

    if not config.getoption("--delete-host", False):
        for item in items:
            if "delete_host" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="Not configured to test host deletion."))

    # legacy code above
    # ''' To enable the test select with `and depends` keyword,
    #     to select test cases and it depended test cases.
    # '''

    if "and depends" not in config.option.keyword:
        # DO nothing
        yield
        return

    all_items, old_keyword = items.copy(), config.option.keyword
    config.option.keyword = old_keyword.replace('and depends', '')

    yield

    scope_cls = {
        "session": pytest.Session,
        "package": pytest.Package,
        "module": pytest.Module,
        "class": pytest.Class
    }
    # ref: https://github.com/RKrahl/pytest-dependency/blob/0.5.1/pytest_dependency.py#L77
    # named_items : dict[('dep-scope', 'dep-name'), list[(idx, 'test-item')]]
    # picked : list[(idx, 'test-item')]
    named_items, picked = dict(), list()
    for idx, item in enumerate(all_items):
        if item in items:
            picked.append((idx, item))
        try:
            marker = item.get_closest_marker('dependency')
            scope = marker.kwargs.get('scope', 'module')
            node = item.getparent(scope_cls[scope])
            named_items.setdefault((node, marker.kwargs['name']), []).append((idx, item))
        except AttributeError:
            continue
        except KeyError:
            nodeid = item.nodeid.replace("::()::", "::")
            if scope not in ("session", "package"):
                shift = 2 if scope == "class" else 1
                nodeid = nodeid.split("::", shift)[shift]
            named_items.setdefault((node, nodeid), []).append((idx, item))

    def pick_depends(idx, item, items):
        picked = []
        try:
            marker = item.get_closest_marker('dependency')
            scope = marker.kwargs.get('scope', 'module')
            node = item.getparent(scope_cls[scope])
            for name in marker.kwargs['depends']:
                picked.extend(items.get((node, name), []))
        except (AttributeError, KeyError):
            pass
        return picked

    depends = []  # list[(idx, 'test-item')]
    while picked:
        depends.append(picked.pop())
        picked.extend(pick_depends(*depends[-1], named_items))

    session.items = items = [it for idx, it in sorted(set(depends), key=lambda it: it[0])]
    # deselected.extend(t for ts in named_items.values() for i, t in ts if t not in items)
    deselected = [t for t in all_items if t not in items]
    # update to let the report shows correct counts
    config.pluginmanager.get_plugin('terminalreporter').stats['deselected'] = deselected
