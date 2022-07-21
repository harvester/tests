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
from scp import SCPClient
import pytest
import subprocess
import time


pytest_plugins = [
    'harvester_e2e_tests.fixtures.vm',
    'harvester_e2e_tests.fixtures.backuptarget'
]


def restart_vm(request, admin_session, harvester_api_endpoints, vm_json):
    timeout = request.config.getoption('--wait-timeout')
    vm_name = vm_json['metadata']['name']
    previous_uid = vm_json['metadata']['uid']
    utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                     vm_name, timeout)


def assert_ssh_into_vm(ip, timeout, keypair=None):
    client = utils.wait_for_ssh_client(ip, timeout, keypair)
    # execute a simple command
    stdin, stdout, stderr = client.exec_command('ls')
    client.close()
    err = stderr.read()
    assert len(err) == 0, ('Error while SSH into %s: %s' % (ip, err))


def fileactions_into_vm(ip, timeout, keypair=None,
                        createfile=None, chkfileexist=None,
                        chkmd5=None, script=None):
    filesPresent = []
    md5pass = []
    client = utils.wait_for_ssh_client(ip, timeout, keypair)
    # execute a simple command
    if script:
        with SCPClient(client.get_transport()) as scp:
            scp.put(script, '/tmp')
        scp.close()
        stdin, stdout, stderr = client.exec_command('ls')
    if createfile:
        stdin, stdout, stderr = client.exec_command(
            'bash /tmp/createFiles.sh {0}'.format(createfile))
    if chkfileexist:
        stdin, stdout, stderr = client.exec_command('ls *.txt 2> /dev/null')
        for line in stdout.readlines():
            filesPresent.append(line.strip())
    if chkmd5:
        stdin, stdout, stderr = client.exec_command('ls *.md5 2> /dev/null')
        for line in stdout.readlines():
            stdin, stdout, stderr = client.exec_command(
                'md5sum --status -c {0} && echo PASS'.format(line.strip()))
            out = stdout.read().strip()
            if out.decode('utf-8') == 'PASS':
                md5pass.append(line.strip())
    client.close()
    err = stderr.read()
    assert len(err) == 0, ('Error while SSH into %s: %s' % (ip, err))
    return (filesPresent, md5pass)


def get_vm_public_ip(admin_session, harvester_api_endpoints, vm, timeout,
                     nic_name='nic-1'):
    return utils.get_vm_ip_address(admin_session, harvester_api_endpoints, vm,
                                   timeout, nic_name=nic_name)


@pytest.mark.virtual_machines_p1
@pytest.mark.p1
def backup_restore_vm(request, admin_session,
                      harvester_api_endpoints,
                      keypair, vms_with_vlan_as_default_network,
                      backuptarget,
                      vm_new=None,
                      new_vm_name=None):
    """
        Test create virutal machines
        Covers:
            virtual-machines-37-Create a VM with Start VM on
            Creation checked
    """
    vm_name = vms_with_vlan_as_default_network['metadata']['name']
    backup_name = utils.random_name()
    backup_json = None
    restored_vm_json = None
    try:
        backup_json = utils.create_vm_backup(request, admin_session,
                                             harvester_api_endpoints,
                                             backuptarget,
                                             name=backup_name,
                                             vm_name=vm_name)
        timeout = request.config.getoption('--wait-timeout')
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints,
            vms_with_vlan_as_default_network, timeout)
        script = utils.get_backup_create_files_script(
            request, 'createFiles.sh', 'backup')
        # Create a file in VM
        fileactions_into_vm(public_ip, timeout,
                            createfile=1,
                            script=script)
        time.sleep(50)
        # Check file exists after taking backup
        fileExists = []
        filesmd5pass = []
        (fileExists, filesmd5pass) = fileactions_into_vm(public_ip, timeout,
                                                         keypair=keypair,
                                                         chkfileexist=True,
                                                         chkmd5=True)
        assert fileExists == ['file1.txt'], 'File1 not exist in VM'
        assert filesmd5pass == ['file1.md5'], 'MD5 chksum failed for file1'

        # Stop VM
        utils.stop_vm(request, admin_session,
                      harvester_api_endpoints, vm_name)
        # Restore existing VM from backup
        restore_name = utils.random_name()
        if new_vm_name:
            vm_name = new_vm_name
        utils.restore_vm_backup(request, admin_session,
                                harvester_api_endpoints,
                                name=restore_name,
                                vm_name=vm_name,
                                backup_name=backup_name,
                                vm_new=vm_new)
        utils.assert_vm_ready(request, admin_session,
                              harvester_api_endpoints,
                              vm_name, running=True)
        resp = admin_session.get(harvester_api_endpoints.get_vm % (
            vm_name))
        assert resp.status_code == 200, 'Failed to get restor VM %s: %s' % (
            vm_name, resp.content)

        restored_vm_json = resp.json()
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints,
            restored_vm_json, timeout)
        if vm_new is None:
            restart_vm(request, admin_session, harvester_api_endpoints,
                       vms_with_vlan_as_default_network)
        fileExists = []
        filesmd5pass = []
        (fileExists, filesmd5pass) = fileactions_into_vm(public_ip, timeout,
                                                         keypair=keypair,
                                                         chkfileexist=True)
        assert len(fileExists) == 0, 'File1 still exist in VM'

    finally:
        if not request.config.getoption('--do-not-cleanup'):
            if backup_json:
                utils.delete_vm(request, admin_session,
                                harvester_api_endpoints,
                                vms_with_vlan_as_default_network)
                utils.delete_vm_backup(request, admin_session,
                                       harvester_api_endpoints,
                                       backuptarget, backup_json)
            if new_vm_name:
                utils.delete_vm(request, admin_session,
                                harvester_api_endpoints, restored_vm_json)


@pytest.mark.network_p2
@pytest.mark.p2
def backup_restore_chained_backups(request, admin_session,
                                   harvester_api_endpoints,
                                   keypair, vms_with_vlan_as_default_network,
                                   backuptarget,
                                   delbackup=None):
    """
       Test Network connectivity and VM
       Covers:
           network-10-Validate network connectivity Mgmt Network
           Delete single network from multiple networks vm
        """

    vm_name = vms_with_vlan_as_default_network['metadata']['name']
    backup_name = utils.random_name()
    backup_lst = []
    backup_json = None
    restored_vm_json = None
    restore_lst = []
    try:
        timeout = request.config.getoption('--wait-timeout')
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints,
            vms_with_vlan_as_default_network, timeout)
        script = utils.get_backup_create_files_script(
            request, 'createFiles.sh', 'backup')
        # scp createFiles script on VM
        fileactions_into_vm(public_ip, timeout,
                            script=script)
        for x in range(1, 4):
            # Create a file in VM
            fileactions_into_vm(public_ip, timeout,
                                createfile=x)
            time.sleep(70)
            backup_name = "bk" + str(x) + "-" + utils.random_name()
            backup_json = utils.create_vm_backup(request, admin_session,
                                                 harvester_api_endpoints,
                                                 backuptarget,
                                                 name=backup_name,
                                                 vm_name=vm_name)
            backup_lst.append(backup_json)

        if delbackup == 'first':
            utils.delete_vm_backup(request, admin_session,
                                   harvester_api_endpoints, backuptarget,
                                   backup_lst[0])
            del backup_lst[0]
        elif delbackup == 'middle':
            utils.delete_vm_backup(request, admin_session,
                                   harvester_api_endpoints, backuptarget,
                                   backup_lst[1])
            del backup_lst[1]
        elif delbackup == 'last':
            utils.delete_vm_backup(request, admin_session,
                                   harvester_api_endpoints, backuptarget,
                                   backup_lst[2])
            del backup_lst[2]
        # Restore backup 1
        # Restore existing VM from backup
        for backup in backup_lst:
            restore_name = utils.random_name()
            utils.stop_vm(request, admin_session,
                          harvester_api_endpoints, vm_name)
            backup_name = backup['metadata']['name']
            utils.restore_vm_backup(request, admin_session,
                                    harvester_api_endpoints,
                                    name=restore_name,
                                    vm_name=vm_name,
                                    backup_name=backup_name)
            utils.assert_vm_ready(request, admin_session,
                                  harvester_api_endpoints,
                                  vm_name, running=True)
            resp = admin_session.get(harvester_api_endpoints.get_vm % (
                vm_name))
            assert resp.status_code == 200, 'Failed to get VM %s: %s' % (
                vm_name, resp.content)

            restored_vm_json = resp.json()
            restore_lst.append(restored_vm_json)
            timeout = request.config.getoption('--wait-timeout')
            (vm_instance_json, public_ip) = get_vm_public_ip(
                admin_session, harvester_api_endpoints,
                restored_vm_json, timeout)
            restart_vm(request, admin_session, harvester_api_endpoints,
                       vms_with_vlan_as_default_network)
            fileExists = []
            filesmd5pass = []
            (fileExists, filesmd5pass) = fileactions_into_vm(public_ip,
                                                             timeout,
                                                             keypair=keypair,
                                                             chkfileexist=True,
                                                             chkmd5=True)
            backup_seq = backup['metadata']['name'].split("-")[0]
            if backup_seq == 'bk1':
                assert fileExists == ['file1.txt'], 'File1 not exist in VM'
                assert filesmd5pass == ['file1.md5'], (
                    'MD5 chksum failed for file1')
            elif backup_seq == 'bk2':
                assert fileExists == ['file1.txt', 'file2.txt'], (
                    'All files dont exist')
                assert filesmd5pass == ['file1-2.md5', 'file2.md5'], (
                    'MD5 ckecksum failed while restoring middle backup')
            elif backup_seq == 'bk3':
                assert fileExists == ['file1.txt', 'file2.txt', 'file3.txt'], (
                    'All files dont exist')
                assert filesmd5pass == [
                    'file1-2.md5', 'file2-2.md5', 'file3.md5'], (
                    'MD5 checksum failed while restoring last backup')
    finally:
        if not request.config.getoption('--do-not-cleanup'):
            if backup_lst:
                utils.delete_vm(request, admin_session,
                                harvester_api_endpoints,
                                vms_with_vlan_as_default_network)
                for backup_json in backup_lst:
                    utils.delete_vm_backup(request, admin_session,
                                           harvester_api_endpoints,
                                           backuptarget, backup_json)


@pytest.mark.network_p1
@pytest.mark.p1
@pytest.mark.public_network
class TestVMNetworking:

    def test_ssh_to_vm(self, request, admin_session,
                       harvester_api_endpoints, keypair,
                       vms_with_vlan_as_default_network):
        """
        Test Network connectivity and VM
        Covers:
            network-01-Validate network connectivity Mgmt Network
            network-08-Validate network connectivity both Mgmt and ext VLAN
            virtual-machines-22-Create a VM with 2 networks,
            one default management network
            and one VLAN
        """
        timeout = request.config.getoption('--wait-timeout')
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints,
            vms_with_vlan_as_default_network, timeout)
        assert_ssh_into_vm(public_ip, timeout, keypair=keypair)

    def test_vlan_ip_pingable_after_reboot(self, request, admin_session,
                                           harvester_api_endpoints, keypair,
                                           vms_with_vlan_as_default_network):
        """
        Negative Test network connectivity after reboot
        Covers:
            network-01-Network Negative Test Case #1: Test VLAN network
            after reboot In this scenario, we want to make sure the
            VLAN IP of a VM is still pingable after the reboot.
        """
        timeout = request.config.getoption('--wait-timeout')
        vm_name = vms_with_vlan_as_default_network['metadata']['name']
        resp = admin_session.get(harvester_api_endpoints.get_vm % (vm_name))
        assert resp.status_code == 200, (
            'Failed to lookup VM %s: %s:%s' % (
                vm_name, resp.status_code, resp.content))
        vm_with_one_vlan = resp.json()

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
        """
        Test Network connectivity
        Covers:
            network-01-Validate network connectivity Mgmt Network
            network-02-Validate network connectivity External VLAN
            network-53-Edit vm network and verify the network is
            working as per configuration
            network-13-Add VLAN network
        """
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
        # reboot the VM as a workaound for
        # https://github.com/harvester/harvester/issues/1059
        restart_vm(request, admin_session, harvester_api_endpoints,
                   updated_vm_data)
        # now make sure we have network connectivity
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints, updated_vm_data, timeout)
        assert_ssh_into_vm(public_ip, timeout, keypair=keypair)

    # NOTE: make sure to run this test case last as the vm_with_one_vlan
    # fixture has a class scope
    def test_remove_vlan_network_from_vm(self, request, admin_session,
                                         harvester_api_endpoints,
                                         vm_with_one_vlan, network):
        """
        Test Network connectivity
        Covers:
            network-12-Delete single network from multiple networks VM
            Delete external VLAN
        """
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
def test_update_vm_management_network_to_vlan(request, admin_session,
                                              harvester_api_endpoints, keypair,
                                              basic_vm, network):
    """
    Test Network connectivity
    Covers:
        network-04-Change management network to external VLAN
    """
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
    """
    Test Network connectivity
    Covers:
        network-06-Change external VLAN to management network
    """
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


@pytest.mark.network_p2
@pytest.mark.p2
@pytest.mark.public_network
def test_vm_network_with_bogus_vlan(request, admin_session,
                                    harvester_api_endpoints,
                                    vm_with_one_bogus_vlan):
    """
    Negative Test creating VM with a bogus VLAN ID
    Covers
        network-04-Invalid network scenario, we expect the VM to be
        successfully created. But the network interface associated
        with the VLAN should not successfully gotten a valid
        IPv4 address.
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
        single_vm = utils.create_vm(
            request, admin_session, image,
            harvester_api_endpoints, keypair=keypair,
            template='vm_with_vlan_as_default_network',
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


@pytest.mark.terraform
@pytest.mark.terraform_provider_p1
@pytest.mark.p1
def test_create_vm_using_terraform(request, admin_session,
                                   harvester_api_endpoints,
                                   image_using_terraform,
                                   volume_using_terraform,
                                   keypair_using_terraform,
                                   network_using_terraform,
                                   user_data_with_guest_agent_using_terraform,
                                   network_data):
    """
    Test creates VM using terraform
    Covers:
    terraform-provider-09-Test harvester_virtualmachine resource
    terraform-provider-01-install, terraform-provider-02-kube config,
    terraform-provider-03-define kube config
    """
    created = False
    try:
        vm_json = utils.create_vm_terraform(
            request,
            admin_session,
            harvester_api_endpoints,
            template_name='resource_vm',
            keypair=keypair_using_terraform,
            image=image_using_terraform,
            volume=volume_using_terraform,
            net=network_using_terraform,
            user_data=user_data_with_guest_agent_using_terraform,
            net_data=network_data)
        created = True
        # make sure the VM instance is successfully created
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        timeout = request.config.getoption('--wait-timeout')
        (vm_instance_json, public_ip) = get_vm_public_ip(
            admin_session, harvester_api_endpoints, vm_json, timeout)
    finally:
        if created:
            if not request.config.getoption('--do-not-cleanup'):
                utils.destroy_resource(request, admin_session, 'all')


@pytest.mark.backup_and_restore_p1
@pytest.mark.p1
@pytest.mark.skip("https://github.com/harvester/harvester/issues/1339")
@pytest.mark.backups3
def test_backup_restore_new_vm(request, admin_session,
                               harvester_api_endpoints,
                               keypair, vm_with_one_vlan,
                               backuptarget_s3,
                               vm_new=True):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-06-Restore Backup Replace New VM
    """
    new_vm_name = "new-vm-" + utils.random_name()
    backup_restore_vm(request, admin_session,
                      harvester_api_endpoints,
                      keypair, vm_with_one_vlan,
                      backuptarget_s3,
                      vm_new=vm_new,
                      new_vm_name=new_vm_name
                      )


@pytest.mark.backup_and_restore_p1
@pytest.mark.p1
@pytest.mark.skip("https://github.com/harvester/harvester/issues/1339")
@pytest.mark.backups3
def test_backup_restore_existing_vm(request, admin_session,
                                    harvester_api_endpoints,
                                    keypair, vm_with_one_vlan,
                                    backuptarget_s3):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-04-Restore Backup Replace existing VM
            with backup from same VM
    """
    backup_restore_vm(request, admin_session,
                      harvester_api_endpoints,
                      keypair, vm_with_one_vlan,
                      backuptarget_s3
                      )


@pytest.mark.backup_and_restore_p1
@pytest.mark.p1
@pytest.mark.skip("https://github.com/harvester/harvester/issues/1339")
@pytest.mark.backups3
def test_chained_del_middle_backup(request, admin_session,
                                   harvester_api_endpoints,
                                   keypair, vm_with_one_vlan,
                                   backuptarget_s3,
                                   delbackup='middle'):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-15-Delete middle backup in chained backup
            backup-and-restore-08-Delete multiple backups
    """
    backup_restore_chained_backups(request, admin_session,
                                   harvester_api_endpoints,
                                   keypair, vm_with_one_vlan,
                                   backuptarget_s3,
                                   delbackup=delbackup
                                   )


@pytest.mark.backup_and_restore_p2
@pytest.mark.p2
@pytest.mark.skip("https://github.com/harvester/harvester/issues/1339")
@pytest.mark.backups3
def test_chained_del_first_backup(request, admin_session,
                                  harvester_api_endpoints,
                                  keypair, vm_with_one_vlan,
                                  backuptarget_s3,
                                  delbackup='first'):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-16-Delete first backup in chained backup
            backup-and-restore-08-Delete multiple backups
    """
    backup_restore_chained_backups(request, admin_session,
                                   harvester_api_endpoints,
                                   keypair, vm_with_one_vlan,
                                   backuptarget_s3,
                                   delbackup=delbackup
                                   )


@pytest.mark.backup_and_restore_p1
@pytest.mark.p1
@pytest.mark.skip("https://github.com/harvester/harvester/issues/1339")
@pytest.mark.backups3
def test_chained_del_last_backup(request, admin_session,
                                 harvester_api_endpoints,
                                 keypair, vm_with_one_vlan,
                                 backuptarget_s3,
                                 delbackup='last'):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-17-Delete last backup in chained backup
            backup-and-restore-08-Delete multiple backups
    """
    backup_restore_chained_backups(request, admin_session,
                                   harvester_api_endpoints,
                                   keypair, vm_with_one_vlan,
                                   backuptarget_s3,
                                   delbackup=delbackup
                                   )


@pytest.mark.backup_and_restore_p1
@pytest.mark.p1
@pytest.mark.skip("https://github.com/harvester/harvester/issues/1339")
@pytest.mark.backups3
def test_restore_chained_backups(request, admin_session,
                                 harvester_api_endpoints,
                                 keypair, vms_with_vlan_as_default_network,
                                 backuptarget_s3):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-18-Delete last backup in chained backup
            backup-and-restore-19-Delete middle backup in chained backup
            backup-and-restore-20-Delete first backup in chained backup
    """
    backup_restore_chained_backups(request, admin_session,
                                   harvester_api_endpoints,
                                   keypair, vms_with_vlan_as_default_network,
                                   backuptarget_s3
                                   )


@pytest.mark.backup_and_restore_p1
@pytest.mark.p1
@pytest.mark.backupnfs
def test_backup_restore_new_vm_nfs(request, admin_session,
                                   harvester_api_endpoints,
                                   keypair, vms_with_vlan_as_default_network,
                                   backuptarget_nfs,
                                   vm_new=True):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-06-Restore Backup Create new VM
    """
    new_vm_name = "new-vm-" + utils.random_name()
    backup_restore_vm(request, admin_session,
                      harvester_api_endpoints,
                      keypair, vms_with_vlan_as_default_network,
                      backuptarget_nfs,
                      vm_new=vm_new,
                      new_vm_name=new_vm_name
                      )


@pytest.mark.backup_and_restore_p1
@pytest.mark.p1
@pytest.mark.backupnfs
def test_backup_restore_existing_vm_nfs(request, admin_session,
                                        harvester_api_endpoints,
                                        keypair,
                                        vms_with_vlan_as_default_network,
                                        backuptarget_nfs):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-04-Restore Backup Replace existing VM nfs
            with backup from same VM
    """
    backup_restore_vm(request, admin_session,
                      harvester_api_endpoints,
                      keypair, vms_with_vlan_as_default_network,
                      backuptarget_nfs
                      )


@pytest.mark.backup_and_restore_p1
@pytest.mark.p1
@pytest.mark.backupnfs
def test_chained_del_middle_backup_nfs(request, admin_session,
                                       harvester_api_endpoints,
                                       keypair,
                                       vms_with_vlan_as_default_network,
                                       backuptarget_nfs,
                                       delbackup='middle'):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-15-Delete middle backup in chained backup nfs
    """
    backup_restore_chained_backups(request, admin_session,
                                   harvester_api_endpoints,
                                   keypair,
                                   vms_with_vlan_as_default_network,
                                   backuptarget_nfs,
                                   delbackup=delbackup
                                   )


@pytest.mark.backup_and_restore_p1
@pytest.mark.p1
@pytest.mark.backupnfs
def test_chained_del_first_backup_nfs(request, admin_session,
                                      harvester_api_endpoints,
                                      keypair,
                                      vms_with_vlan_as_default_network,
                                      backuptarget_nfs,
                                      delbackup='first'):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-16-Delete first backup in chained backup nfs
    """
    backup_restore_chained_backups(request, admin_session,
                                   harvester_api_endpoints,
                                   keypair,
                                   vms_with_vlan_as_default_network,
                                   backuptarget_nfs,
                                   delbackup=delbackup
                                   )


@pytest.mark.backup_and_restore_p1
@pytest.mark.p1
@pytest.mark.backupnfs
def test_chained_del_last_backup_nfs(request, admin_session,
                                     harvester_api_endpoints,
                                     keypair,
                                     vms_with_vlan_as_default_network,
                                     backuptarget_nfs,
                                     delbackup='last'):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-17-Delete last backup in chained backup nfs
    """
    backup_restore_chained_backups(request, admin_session,
                                   harvester_api_endpoints,
                                   keypair, vms_with_vlan_as_default_network,
                                   backuptarget_nfs,
                                   delbackup=delbackup
                                   )


@pytest.mark.backup_and_restore_p1
@pytest.mark.p1
@pytest.mark.backupnfs
def test_restore_chained_backups_nfs(request, admin_session,
                                     harvester_api_endpoints,
                                     keypair,
                                     vms_with_vlan_as_default_network,
                                     backuptarget_nfs):
    """
        Backup Restore Testing
        Covers:
            backup-and-restore-18-Delete last backup in chained backup nfs
            backup-and-restore-19-Delete middle backup in chained backup nfs
            backup-and-restore-20-Delete first backup in chained backup nfs
    """
    backup_restore_chained_backups(request, admin_session,
                                   harvester_api_endpoints,
                                   keypair,
                                   vms_with_vlan_as_default_network,
                                   backuptarget_nfs
                                   )
