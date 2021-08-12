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


def wait_for_ssh_client(ip, timeout, keypair=None):
    client = SSHClient()
    # automatically add host since we only care about connectivity
    client.set_missing_host_key_policy(AutoAddPolicy)

    def _wait_for_connect():
        try:
            # NOTE: for the default openSUSE Leap image, the root user
            # password is 'linux'
            if keypair is not None:
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
    return client


def assert_ssh_into_vm(ip, timeout, keypair=None):
    client = wait_for_ssh_client(ip, timeout, keypair)
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

    def test_vlan_ip_pingable_after_reboot(self, request, admin_session,
                                           harvester_api_endpoints, keypair,
                                           vm_with_one_vlan):
        """ Network Negative Test Case #1: Test VLAN network after reboot

        In this scenario, we want to make sure the VLAN IP of a VM is still
        pingable after the reboot.
        """
        timeout = request.config.getoption('--wait-timeout')
        vm_name = vm_with_one_vlan['metadata']['name']
        previous_uid = vm_with_one_vlan['metadata']['uid']
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints, vm_with_one_vlan, timeout)
        # make sure the public_ip is pingable
        assert subprocess.call(['ping', '-c', '3', public_ip]) == 0, (
            'Failed to ping VM %s public IP %s' % (vm_name, public_ip))
        # reboot the instance
        utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                         vm_name, timeout)
        # make sure the public_ip is pingable
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints, vm_with_one_vlan, timeout)
        assert subprocess.call(['ping', '-c', '3', public_ip]) == 0, (
            'Failed to ping VM %s public IP %s' % (vm_name, public_ip))

    def test_add_vlan_network_to_vm(self, request, admin_session,
                                    harvester_api_endpoints, basic_vm,
                                    network, keypair):
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
        assert_ssh_into_vm(public_ip, timeout, keypair=keypair)

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


@pytest.mark.public_network
def test_two_vms_on_same_vlan(request, admin_session,
                              harvester_api_endpoints, keypair,
                              vms_with_same_vlan, network):
    timeout = request.config.getoption('--wait-timeout')
    network_name = network['metadata']['name']
    for vm_json in vms_with_same_vlan:
        # make sure the VM is on the same VLAN
        networks = vm_json['spec']['template']['spec']['networks']
        match_network = [n for n in networks if (n['name'] == 'nic-1')]
        assert len(match_network) == 1, (
            'Found multiple network interfaces with name "nic-1"')
        assert 'multus' in match_network[0], (
            'Expecting "multus" network interface.')
        assert match_network[0]['multus']['networkName'] == network_name, (
            'Expecting network name %s, got %s instead.' % (
                network_name, match_network[0]['multus']['networkName']))
        # now make sure it has connectivity
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints, vm_json, timeout)
        assert_ssh_into_vm(public_ip, timeout, keypair=keypair)


@pytest.mark.public_network
def test_management_ip_pingable_after_reboot(request, admin_session,
                                             harvester_api_endpoints, keypair,
                                             vms_with_same_vlan):
    """ Network Negative Test Case #2: Test management network after reboot

    In this scenario, we want to make sure the management IP of a VM is still
    pingable from another VM on the same subnet after the reboot.
    """
    timeout = request.config.getoption('--wait-timeout')
    # get the public IP of the first VM so we can SSH into it and ping the
    # second VM's management IP as the management IP is on a private subnet
    (vm_instance_json, public_ip) = get_vm_public_ip(
        admin_session, harvester_api_endpoints, vms_with_same_vlan[0], timeout)
    # wait for the second VM to fully boot up as well
    (second_vm_instance, second_public_ip) = get_vm_public_ip(
        admin_session, harvester_api_endpoints, vms_with_same_vlan[1], timeout)
    # get the management IP of the second VM
    # NOTE: the first interface is the management IP
    ip = second_vm_instance['status']['interfaces'][0]['ipAddress']
    client = wait_for_ssh_client(public_ip, timeout, keypair=keypair)
    # make sure the management IP of the second VM is pingable from the
    # first VM
    stdin, stdout, stderr = client.exec_command('ping -c 3 %s' % (ip))
    client.close()
    err = stderr.read()
    assert len(err) == 0, ('Unable to ping %s: %s' % (ip, err))
    # reboot the second VM
    vm_name = vms_with_same_vlan[1]['metadata']['name']
    previous_uid = vms_with_same_vlan[1]['metadata']['uid']
    utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                     vm_name, timeout)
    # make sure the management IP of the second VM still pingable from
    # the first VM after reboot
    client = wait_for_ssh_client(public_ip, timeout, keypair=keypair)
    stdin, stdout, stderr = client.exec_command('ping -c 3 %s' % (ip))
    client.close()
    err = stderr.read()
    assert len(err) == 0, ('Unable to ping %s after reboot: %s' % (ip, err))


@pytest.mark.public_network
def test_update_vm_management_network_to_vlan(request, admin_session,
                                              harvester_api_endpoints, keypair,
                                              basic_vm, network):
    vm_name = basic_vm['metadata']['name']
    previous_uid = basic_vm['metadata']['uid']
    timeout = request.config.getoption('--wait-timeout')
    # update VM to use VLAN as it's default network
    basic_vm['spec']['template']['spec']['domain']['devices']['interfaces'] = [
        {
            'bridge': {},
            'model': 'virtio',
            'name': 'nic-1'
        }
    ]
    basic_vm['spec']['template']['spec']['networks'] = [
        {
            'multus': {
                'networkName': network['metadata']['name']
            },
            'name': 'nic-1'
        }
    ]
    resp = utils.poll_for_update_resource(
        request, admin_session,
        harvester_api_endpoints.update_vm % (vm_name),
        basic_vm,
        harvester_api_endpoints.get_vm % (vm_name))
    updated_vm_data = resp.json()
    # restart the VM instance for the changes to take effect
    utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                     vm_name, timeout)
    # make sure it has only one interface
    updated_spec = updated_vm_data['spec']['template']['spec']
    num_interfaces = len(updated_spec['domain']['devices']['interfaces'])
    assert num_interfaces == 1, (
        'Expecting one interface, got %s instead: %s' % (
            num_interfaces, updated_spec['domain']['devices']['interfaces']))
    # it should have a public IP
    (vm_instance_json, public_ip) = get_vm_public_ip(
        admin_session, harvester_api_endpoints, updated_vm_data, timeout)
    # make sure it has connectivity
    assert_ssh_into_vm(public_ip, timeout, keypair=keypair)


@pytest.mark.public_network
def test_update_vm_vlan_network_to_management(request, admin_session,
                                              harvester_api_endpoints, keypair,
                                              vms_with_vlan_as_default_network,
                                              network):
    vm_name = vms_with_vlan_as_default_network['metadata']['name']
    previous_uid = vms_with_vlan_as_default_network['metadata']['uid']
    timeout = request.config.getoption('--wait-timeout')
    # make sure it has only the public IP
    spec = vms_with_vlan_as_default_network['spec']['template']['spec']
    num_interfaces = len(spec['domain']['devices']['interfaces'])
    assert num_interfaces == 1, (
        'Expecting one interface, got %s instead: %s' % (
            num_interfaces, spec['domain']['devices']['interfaces']))
    (vm_instance_json, public_ip) = get_vm_public_ip(
        admin_session, harvester_api_endpoints,
        vms_with_vlan_as_default_network, timeout)
    # now update VM to use default management interface only
    spec['domain']['devices']['interfaces'] = [
        {
            'masquerade': {},
            'model': 'virtio',
            'name': 'default'
        }
    ]
    spec['networks'] = [
        {
            'name': 'default',
            'pod': {}
        }
    ]
    resp = utils.poll_for_update_resource(
        request, admin_session,
        harvester_api_endpoints.update_vm % (vm_name),
        vms_with_vlan_as_default_network,
        harvester_api_endpoints.get_vm % (vm_name))
    updated_vm_data = resp.json()
    # restart the VM instance for the changes to take effect
    utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                     vm_name, timeout)
    # make sure the instance has only one IP in 10.52.0.0/24 subnet
    vm_instance_json = utils.lookup_vm_instance(
        admin_session, harvester_api_endpoints, updated_vm_data)
    num_interfaces = len(vm_instance_json['status']['interfaces'])
    assert num_interfaces == 1, (
        'Expecting one interface, got %s instead: %s' % (
            num_interfaces, vm_instance_json['status']['interfaces']))
    assert vm_instance_json['status']['interfaces'][0]['name'] == 'default', (
        'Expecting interface name to be "default", got %s instead' % (
            vm_instance_json['status']['interfaces'][0]['name']))
    ip = vm_instance_json['status']['interfaces'][0]['ipAddress']
    assert ip.startswith('10.52.'), (
        'Expecting IP address to be in 10.52.0.0/24 subnet, got %s instead' % (
            ip))


@pytest.mark.public_network
def test_vm_network_with_bogus_vlan(request, admin_session,
                                    harvester_api_endpoints,
                                    vm_with_one_bogus_vlan):
    """ Test creating VM with a bogus VLAN ID

    In this scenario, we expect the VM to be successfully created. But the
    network interface associated with the VLAN should not successfully gotten
    a valid IPv4 address.
    """
    timeout = request.config.getoption('--wait-timeout')
    (vm_instance_json, public_ip) = get_vm_public_ip(
        admin_session, harvester_api_endpoints,
        vm_with_one_bogus_vlan, timeout)
    # the VM instance should not be getting a IPv4 address
    ip_parts = public_ip.split('.')
    assert len(ip_parts) != 4, (
        'VM should not have gotten an IPv4 address. Got %s' % (public_ip))


@pytest.mark.public_network
def test_create_update_vm_user_data(request, admin_session, image,
                                    keypair, harvester_api_endpoints, network,
                                    user_data_with_guest_agent, network_data):
    created = False
    try:
        single_vm = utils.create_vm(request, admin_session, image,
                                    harvester_api_endpoints, keypair=keypair,
                                    template='vm_with_one_vlan',
                                    network=network)
        created = True
        # make sure the VM instance is successfully created
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, single_vm)
        vm_name = single_vm['metadata']['name']
        previous_uid = vm_instance_json['metadata']['uid']
        devices = (
            single_vm['spec']['template']['spec']['domain']['devices']['disks']
            )
        device_data = {
            'disk': {
                'bus': 'virtio'
            },
            'name': 'cloudinitdisk'
        }
        devices.append(device_data)
        vol_data = single_vm['spec']['template']['spec']['volumes']
        assert 'cloudInitNoCloud' not in vol_data
        userdata = user_data_with_guest_agent.replace('\\n', '\n')
        netdata = network_data.replace('\\n', '\n')
        user_data = {
            'cloudInitNoCloud': {
                'networkData': netdata,
                'userData': userdata
                },
            'name': 'cloudinitdisk'
        }
        vol_data.append(user_data)
        resp = utils.poll_for_update_resource(
            request, admin_session,
            harvester_api_endpoints.update_vm % (vm_name),
            single_vm,
            harvester_api_endpoints.get_vm % (vm_name),
            use_yaml=True)
        # restart the VM instance for the updated machine type to take effect
        utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                         vm_name, request.config.getoption('--wait-timeout'))
        resp = admin_session.get(harvester_api_endpoints.get_vm % (
            vm_name))
        updated_data = resp.json()
        updated_vol_data = updated_data['spec']['template']['spec']['volumes']
        found = False
        for i in updated_vol_data:
            if i['name'] == 'cloudinitdisk':
                if (i['cloudInitNoCloud']['networkData'] == netdata and
                        i['cloudInitNoCloud']['userData'] == userdata):
                    found = True
                    break

        assert found, 'Failed to update VM %s to add userDate & NetData' % (
            vm_name)

        timeout = request.config.getoption('--wait-timeout')
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints, updated_data, timeout)
        assert_ssh_into_vm(public_ip, timeout, keypair=keypair)
    finally:
        if created:
            if not request.config.getoption('--do-not-cleanup'):
                utils.delete_vm(request, admin_session,
                                harvester_api_endpoints, single_vm)
