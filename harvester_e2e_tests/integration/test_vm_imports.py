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
from harvester_e2e_tests import utils
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep

import json
import re
import pytest
import yaml
from paramiko.ssh_exception import ChannelException

pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_client',
    'harvester_e2e_tests.fixtures.vm_imports',
    'harvester_e2e_tests.fixtures.images',
    'harvester_e2e_tests.fixtures.virtualmachines'
]


@pytest.fixture(scope="session")
def virtctl(api_client):
    code, ctx = api_client.vms.download_virtctl()

    with NamedTemporaryFile("wb") as f:
        f.write(ctx)
        f.seek(0)
        yield Path(f.name)


@pytest.fixture(scope="session")
def kubeconfig_file(api_client):
    kubeconfig = api_client.generate_kubeconfig()
    with NamedTemporaryFile("w") as f:
        f.write(kubeconfig)
        f.seek(0)
        yield Path(f.name)

@pytest.fixture(scope='module')
def vlan_network_openstack(request, api_client):
    vlan_nic = request.config.getoption('--vlan-nic')
    vlan_id = request.config.getoption('--vlan-id')
    assert -1 != vlan_id, "OpenStack integration test needs VLAN"

    api_client.clusternetworks.create(vlan_nic)
    api_client.clusternetworks.create_config(vlan_nic, vlan_nic, vlan_nic)

    network_name = f'os-{vlan_id}'
    code, data = api_client.networks.get(network_name)
    if code != 200:
        code, data = api_client.networks.create(network_name, vlan_id, cluster_network=vlan_nic)
        assert 201 == code, (
            f"Failed to create network-attachment-definition {network_name} \
                with error {code}, {data}"
        )

    data['id'] = data['metadata']['name']
    yield data

    api_client.networks.delete(network_name)


@pytest.fixture(scope="module")
def image_ubuntu_jammy(api_client, image_jammy, unique_name, wait_timeout):
    unique_image_id = f'image-{unique_name}'
    code, data = api_client.images.create_by_url(
        unique_image_id, image_jammy.url, display_name=f"{unique_name}-{image_jammy.name}"
    )

    assert 201 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(unique_image_id)
        if 100 == data.get('status', {}).get('progress', 0):
            break
        sleep(3)
    else:
        raise AssertionError(
            "Failed to create Image with error:\n"
            f"Status({code}): {data}"
        )

    yield dict(id=f"{data['metadata']['namespace']}/{unique_image_id}",
               user=image_jammy.ssh_user)

    code, data = api_client.images.delete(unique_image_id)


@pytest.fixture(scope="module")
def unique_vm_name(unique_name):
    return f"vm-{unique_name}"

@pytest.fixture(scope="module")
def openstack_vm(api_client, image_ubuntu_jammy, unique_vm_name, wait_timeout, user_data_openstack, vlan_network_openstack):
    """
    tbd...
    """
    cpu, mem = 6, 12
    vm = api_client.vms.Spec(cpu, mem, description="OpenStack VM", guest_agent=False)
    vm.add_image("disk-0", image_ubuntu_jammy['id'])
    vm.add_network('nic-0', vlan_network_openstack['id'])
    vm.user_data = user_data_openstack

    code, data = api_client.vms.create(unique_vm_name, vm)

    assert 201 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_vm_name)
        if 200 == code and "Running" == data.get('status', {}).get('phase'):
            break
        sleep(3)
    else:
        raise AssertionError(
            f"Failed to create OpenStack VM({cpu} core, {mem} RAM) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

    yield unique_vm_name

    api_client.vms.delete(unique_vm_name)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_vm_name)
        if 404 == code:
            break
        sleep(3)


@pytest.mark.p0
class TestOpenStackSetup:

    @pytest.mark.dependency(name="openstack_openrc")
    def test_openstack_openrc(self, api_client, openstack_vm, wait_timeout, vm_shell):
        """
        Test...
        """
        # make sure the VM instance is successfully created
        code, data = api_client.vms.get(openstack_vm)
        assert 200 == code
        assert "Running" == data['status']['printableStatus']
        #vm_shell = vm_shell.login(data['status']['interfaces'][0]['ipAddress'], user="root", password="linux")
        pass
        # find some way to get clouds.yaml file https://192.168.9.90/project/api_access/clouds.yaml/
        # This is a clouds.yaml file, which can be used by OpenStack tools as a source
        # of configuration on how to connect to a cloud. If this is your only cloud,
        # just put this file in ~/.config/openstack/clouds.yaml and tools like
        # python-openstackclient will just work with no further config. (You will need
        # to add your password to the auth section)
        # If you have more than one cloud account, add the cloud entry to the clouds
        # section of your existing file and you can refer to them by name with
        # OS_CLOUD=openstack or --os-cloud=openstack
        # clouds:
        #   openstack:
        #     auth:
        #       auth_url: https://192.168.9.90:5000/v3/
        #       username: "admin"
        #       project_id: 63c9628764e54f9a913af16c472bb7e8
        #       project_name: "admin"
        #       user_domain_name: "Default"
        #     region_name: "microstack"
        #     interface: "public"
        #     identity_api_version: 3
#         ubuntu@node4:~$ openstack project list --user admin -f json
# [
#   {
#     "ID": "63c9628764e54f9a913af16c472bb7e8",
#     "Name": "admin"
#   }
# ]
