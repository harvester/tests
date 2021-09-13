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

from harvester_e2e_tests import utils
import pytest


pytest_plugins = [
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.keypair',
    'harvester_e2e_tests.fixtures.network',
    'harvester_e2e_tests.fixtures.volume'
]


@pytest.fixture(scope='class')
def network_data():
    yaml_data = """#cloud-config
version: 1
config:
  - type: physical
    name: eth0
    subnets:
      - type: dhcp
  - type: physical
    name: eth1
    subnets:
      - type: dhcp
"""
    return yaml_data.replace('\n', '\\n')


@pytest.fixture(scope='class')
def user_data_with_guest_agent(keypair):
    # set to root user password to 'linux' to test password login in
    # addition to SSH login
    yaml_data = """#cloud-config
chpasswd:
  list: |
    root:linux
  expire: false
ssh_pwauth: true
users:
  - name: root
    ssh_authorized_keys:
      - %s
package_update: true
packages:
  - qemu-guest-agent
runcmd:
  - - systemctl
    - enable
    - '--now'
    - qemu-ga
""" % (keypair['spec']['publicKey'])
    return yaml_data.replace('\n', '\\n')


@pytest.fixture(scope='class')
def basic_vm(request, admin_session, image, keypair,
             user_data_with_guest_agent, network_data,
             harvester_api_endpoints):
    vm_json = utils.create_vm(request, admin_session, image,
                              harvester_api_endpoints,
                              keypair=keypair,
                              network_data=network_data,
                              user_data=user_data_with_guest_agent)
    yield vm_json
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.get(
            harvester_api_endpoints.get_vm % (vm_json['metadata']['name']))
        if resp.status_code != 404:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


@pytest.fixture(scope='class')
def basic_vm_no_user_data(request, admin_session, image, keypair,
                          network_data, harvester_api_endpoints):
    vm_json = utils.create_vm(request, admin_session, image,
                              harvester_api_endpoints,
                              keypair=keypair,
                              network_data=network_data)
    yield vm_json
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.get(
            harvester_api_endpoints.get_vm % (vm_json['metadata']['name']))
        if resp.status_code != 404:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


@pytest.fixture(scope='class')
def basic_vm_nousb(request, admin_session, image, keypair,
                   user_data_with_guest_agent, network_data,
                   harvester_api_endpoints):
    vm_json = utils.create_vm(request, admin_session, image,
                              harvester_api_endpoints,
                              keypair=keypair,
                              network_data=network_data,
                              user_data=user_data_with_guest_agent,
                              include_usb=False)
    yield vm_json
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.get(
            harvester_api_endpoints.get_vm % (vm_json['metadata']['name']))
        if resp.status_code != 404:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


@pytest.fixture(scope='class')
def vm_with_one_vlan(request, admin_session, image, keypair,
                     user_data_with_guest_agent, network_data,
                     harvester_api_endpoints, network):
    vm_json = utils.create_vm(request, admin_session, image,
                              harvester_api_endpoints,
                              keypair=keypair,
                              template='vm_with_one_vlan',
                              network=network,
                              network_data=network_data,
                              user_data=user_data_with_guest_agent)
    yield vm_json
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.get(
            harvester_api_endpoints.get_vm % (vm_json['metadata']['name']))
        if resp.status_code != 404:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


@pytest.fixture(scope='class')
def vm_with_one_bogus_vlan(request, admin_session, image, keypair,
                           user_data_with_guest_agent, network_data,
                           harvester_api_endpoints, bogus_network):
    vm_json = utils.create_vm(request, admin_session, image,
                              harvester_api_endpoints,
                              keypair=keypair,
                              template='vm_with_one_vlan',
                              network=bogus_network,
                              network_data=network_data,
                              user_data=user_data_with_guest_agent)
    yield vm_json
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.get(
            harvester_api_endpoints.get_vm % (vm_json['metadata']['name']))
        if resp.status_code != 404:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


@pytest.fixture(scope='class')
def vms_with_same_vlan(request, admin_session, image, keypair,
                       user_data_with_guest_agent, network_data,
                       harvester_api_endpoints, network):
    vms = []
    for i in range(2):
        vms.append(utils.create_vm(request, admin_session, image,
                                   harvester_api_endpoints,
                                   keypair=keypair,
                                   template='vm_with_one_vlan',
                                   network=network,
                                   network_data=network_data,
                                   user_data=user_data_with_guest_agent))
    yield vms
    if not request.config.getoption('--do-not-cleanup'):
        for vm_json in vms:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


@pytest.fixture(scope='class')
def vms_with_vlan_as_default_network(request, admin_session, image, keypair,
                                     user_data_with_guest_agent, network_data,
                                     harvester_api_endpoints, network):
    vm_json = utils.create_vm(request, admin_session, image,
                              harvester_api_endpoints,
                              keypair=keypair,
                              template='vm_with_vlan_as_default_network',
                              network=network,
                              network_data=network_data,
                              user_data=user_data_with_guest_agent)
    yield vm_json
    if not request.config.getoption('--do-not-cleanup'):
        utils.delete_vm(request, admin_session, harvester_api_endpoints,
                        vm_json)


@pytest.fixture(scope='class')
def vm_with_volume(request, admin_session, image, volume, keypair,
                   harvester_api_endpoints):
    vm_json = utils.create_vm(request, admin_session, image,
                              harvester_api_endpoints,
                              template='vm_with_volume',
                              volume=volume,
                              keypair=keypair)
    return vm_json
