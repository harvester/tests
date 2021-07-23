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
from io import StringIO
from paramiko import SSHClient, AutoAddPolicy, RSAKey
import polling2
import pytest
import subprocess

pytest_plugins = [
    'harvester_e2e_tests.fixtures.vm'
]


def assert_ssh_into_vm(ip, timeout, keypair=None):
    client = SSHClient()
    # automatically add host since we only care about connectivity
    client.set_missing_host_key_policy(AutoAddPolicy)

    def _wait_for_connect():
        try:
            # NOTE: for the default openSUSE Leap image, the root user
            # password is 'linux'
            if keypair:
                private_key = RSAKey.from_private_key(
                    StringIO(keypair['spec']['privateKey']))
                client.connect(ip, username='root', pkey=private_key)
            else:
                client.connect(ip, username='root', password='linux')
        except Exception as e:
            print('Unable to load private key: %s' % (
                keypair['spec']['privateKey']))
            print(e)
            return False
        return True

    ready = polling2.poll(
        _wait_for_connect,
        step=5,
        timeout=timeout)
    assert ready, 'Timed out while waiting for SSH server to be ready'
    # execute a simple command
    stdin, stdout, stderr = client.exec_command('ls')
    client.close()
    err = stderr.read()
    assert len(err) == 0, ('Error while SSH into %s: %s' % (ip, err))


def get_vm_public_ip(admin_session, harvester_api_endpoints, vm, timeout,
                     nic_name='nic-1'):
    vm_instance_json = None
    public_ip = None

    def _wait_for_public_ip_available():
        nonlocal vm_instance_json, public_ip
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm)
        for interface in vm_instance_json['status']['interfaces']:
            # NOTE: by default, the second NIC name is 'nic-1'
            if (interface['name'] == nic_name and
                    'ipAddress' in interface):
                public_ip = interface['ipAddress']
                return True
        return False

    ready = polling2.poll(
        _wait_for_public_ip_available,
        step=5,
        timeout=timeout)

    assert ready, (
        'Timed out while waiting for VM public IP to be assigned: %s' % (
            vm_instance_json))
    return (vm_instance_json, public_ip)


@pytest.mark.public_network
class TestVMNetworking:

    def test_ssh_to_vm(self, request, admin_session,
                       harvester_api_endpoints, keypair, vm_with_one_vlan):
        timeout = request.config.getoption('--wait-timeout')
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints, vm_with_one_vlan, timeout)
        assert_ssh_into_vm(public_ip, timeout, keypair=keypair)

    def test_add_vlan_network_to_vm(self, request, admin_session,
                                    harvester_api_endpoints, basic_vm,
                                    network):
        vm_name = basic_vm['metadata']['name']
        previous_uid = basic_vm['metadata']['uid']
        timeout = request.config.getoption('--wait-timeout')
        # add a new network to the VM
        network_name = 'nic-1'
        new_network = {
            'name': network_name,
            'multus': {'networkName': network['metadata']['name']}
        }
        new_network_interface = {
            'bridge': {},
            'model': 'virtio',
            'name': network_name
        }
        spec = basic_vm['spec']['template']['spec']
        if 'interfaces' not in spec['domain']['devices']:
            spec['domain']['devices']['interfaces'] = []
        spec['domain']['devices']['interfaces'].append(new_network_interface)
        if 'networks' not in spec:
            spec['networks'] = []
        spec['networks'].append(new_network)
        resp = utils.poll_for_update_resource(
            request, admin_session,
            harvester_api_endpoints.update_vm % (vm_name),
            basic_vm,
            harvester_api_endpoints.get_vm % (vm_name))
        updated_vm_data = resp.json()
        # restart the VM instance for the changes to take effect
        utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                         vm_name, request.config.getoption('--wait-timeout'))
        # check to make sure the network device is in the updated spec
        found = False
        updated_spec = updated_vm_data['spec']['template']['spec']
        for i in updated_spec['domain']['devices']['interfaces']:
            if (network_name == i['name'] and i['model'] == 'virtio' and
                    'bridge' in i):
                found = True
                break
        assert found, 'Failed to add new network device to VM %s' % (vm_name)
        # check to make sure network is in the updated spec
        found = False
        for n in updated_spec['networks']:
            if network_name == n['name']:
                found = True
                break
        assert found, 'Failed to add new network to VM %s' % (vm_name)
        # now make sure we have network connectivity
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints, updated_vm_data, timeout)
        assert_ssh_into_vm(public_ip, timeout)

    # NOTE: make sure to run this test case last as the vm_with_one_vlan
    # fixture has a class scope
    def test_remove_vlan_network_from_vm(self, request, admin_session,
                                         harvester_api_endpoints,
                                         vm_with_one_vlan, network):
        vm_name = vm_with_one_vlan['metadata']['name']
        previous_uid = vm_with_one_vlan['metadata']['uid']
        timeout = request.config.getoption('--wait-timeout')
        # wait for the VM to boot with a public IP
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints, vm_with_one_vlan, timeout)
        # now remove the second (public IP) NIC from the VM and reboot
        spec = vm_with_one_vlan['spec']['template']['spec']
        interfaces = spec['domain']['devices']['interfaces']
        spec['domain']['devices']['interfaces'] = [
            i for i in interfaces if not (i['name'] == 'nic-1')]
        networks = spec['networks']
        spec['networks'] = [n for n in networks if not (n['name'] == 'nic-1')]
        resp = utils.poll_for_update_resource(
            request, admin_session,
            harvester_api_endpoints.update_vm % (vm_name),
            vm_with_one_vlan,
            harvester_api_endpoints.get_vm % (vm_name))
        updated_vm_data = resp.json()
        # restart the VM instance for the changes to take effect
        utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                         vm_name, request.config.getoption('--wait-timeout'))
        # check to make sure the second NIC's been removed
        found = False
        updated_spec = updated_vm_data['spec']['template']['spec']
        for i in updated_spec['domain']['devices']['interfaces']:
            if i['name'] == 'nic-1':
                found = True
                break
        assert not found, 'Failed to remove network interface from VM %s' % (
            vm_name)
        # make sure it's public IP is no longer pingable
        assert subprocess.call(['ping', '-c', '3', public_ip]) != 0, (
            'Failed to remove network interface from VM %s. Public IP %s '
            'still accessible.' % (vm_name, public_ip))
