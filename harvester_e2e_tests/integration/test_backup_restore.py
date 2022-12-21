# Copyright (c) 2022 SUSE LLC
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
import time
from datetime import datetime, timedelta


pytest_plugins = [
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.api_client',
    'harvester_e2e_tests.fixtures.virtualmachines'
]

IMAGE_URL = 'https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img'
VMI_PATH = '%s/apis/kubevirt.io/v1/namespaces/default/virtualmachineinstances/%s'
USERNAME = 'ubuntu'
PASSWORD = '123456'


@pytest.fixture(scope='module')
def need_cleanup(request):
    return not request.config.getoption('--do-not-cleanup', False)


@pytest.fixture(scope='module')
def endpoint(request):
    return request.config.getoption('--endpoint')


@pytest.fixture(scope='module')
def endpoint_ip(endpoint):
    return endpoint[8:].split(':')[0]


def _wait_for_vm_ready(api_client, wait_timeout, vm_name):
    end_time = datetime.now() + timedelta(seconds=wait_timeout)

    code, data = api_client.vms.get_status(vm_name)
    assert 200 == code or 404 == code, (
        f'Failed to get VM {vm_name} status: {data}')

    while datetime.now() < end_time:
        if 404 != code:
            phase = data.get('status', {}).get('phase')
            conditions = data.get('status', {}).get('conditions', [])

            if (phase == 'Running' and
                conditions and
                    conditions[-1]['type'] == 'AgentConnected'):
                break
        time.sleep(3)

        code, data = api_client.vms.get_status(vm_name)
        assert 200 == code or 404 == code, (
            f'Failed to get VM {vm_name} status: {data}')
    assert datetime.now() < end_time, (
        f'Time-out waiting for VM {vm_name} to be ready.')


def _wait_for_vm_stop(api_client, wait_timeout, vm_name):
    end_time = datetime.now() + timedelta(seconds=wait_timeout)
    api_client.vms.stop(vm_name)

    code, vm = api_client.vms.get(vm_name)
    assert 200 == code, (
        f'Failed to get VM {vm_name}: {vm}')

    while datetime.now() < end_time:
        status = vm.get('status', {}).get('printableStatus')
        if status == 'Stopped':
            break
        time.sleep(3)

        code, vm = api_client.vms.get(vm_name)
        assert 200 == code, (
            f'Failed to get VM {vm_name}: {vm}')
    assert datetime.now() < end_time, (
        f'Time-out waiting for VM {vm_name} to stop.')


def _wait_for_image_ready(wait_timeout, api_client, name):
    end_time = datetime.now() + timedelta(seconds=wait_timeout)

    code, image = api_client.images.get(name)
    assert 200 == code, (
        f'Failed to get image {name}: {image}')
    while datetime.now() < end_time:
        progress = image.get('status', {}).get('progress', 0)
        if progress == 100:
            break
        time.sleep(3)

        code, image = api_client.images.get(name)
        assert 200 == code, (
            f'Failed to get image {name}: {image}')
    assert datetime.now() < end_time, (
        f'Time-out waiting for image {name} to be ready.')


def _find_ip_address_in_vmi(vmi):
    if 'interfaces' not in vmi['status']:
        return ''

    interfaces = vmi['status']['interfaces']
    if len(interfaces) == 0:
        return ''

    default_nic = None
    for interface in interfaces:
        if interface['name'] is not None and interface['name'] == 'default':
            default_nic = interface
            break
    if default_nic is None or 'ipAddress' not in default_nic:
        return ''
    return default_nic['ipAddress']


def _wait_for_backup_ready(wait_timeout, api_client, backup_name):
    end_time = datetime.now() + timedelta(seconds=wait_timeout)

    code, backup = api_client.backups.get(backup_name)
    assert 200 == code, (
        f'Failed to get backup {backup_name}: {backup}')
    while datetime.now() < end_time:
        ready = backup.get('status', {}).get('readyToUse', False)
        if ready:
            break
        time.sleep(3)

        code, backup = api_client.backups.get(backup_name)
        assert 200 == code, (
            f'Failed to get backup {backup_name}: {backup}')
    assert datetime.now() < end_time, (
        f'Timed-out waiting for the backup \'{backup_name}\' to be ready.')


def _check_file_integrity(vm_shell, filename):
    stdout_existence, _ = (
        vm_shell.exec_command(f'if [[ -f \'{filename}\' ]]; then echo yes; fi'))
    if 'yes' not in stdout_existence:
        return False

    stdout_existence_md5, _ = (
        vm_shell.exec_command(f'if [[ -f \'{filename}.md5\' ]]; then echo yes; fi'))
    if 'yes' not in stdout_existence_md5:
        return False

    stdout_md5, _ = vm_shell.exec_command(f'md5sum -c {filename}.md5')
    return f'{filename}: OK' in stdout_md5


def _create_random_file_with_md5(vm_shell, filename):
    vm_shell.exec_command(f'dd if=/dev/urandom of={filename} bs=1M count=4')
    stdout_create_file, _ = (
        vm_shell.exec_command(f'if [[ -f {filename} ]]; then echo yes; fi'))
    assert 'yes' in stdout_create_file, (
        f'Failed to create file {filename}')

    vm_shell.exec_command(f'md5sum {filename} > {filename}.md5')
    stdout_md5, _ = (
        vm_shell.exec_command(f'if [[ -f {filename}.md5 ]]; then echo yes; fi'))
    assert 'yes' in stdout_md5, (
        f'Failed to create file md5sum {filename}.md5')

    vm_shell.exec_command('sync')


def _get_vmi(endpoint, api_client, name, wait_timeout):
    end_time = datetime.now() + timedelta(seconds=wait_timeout)

    vmi_path = VMI_PATH % (endpoint, name)
    response = api_client._get(vmi_path)
    code = response.status_code
    vmi = response.json()
    while datetime.now() < end_time:
        if code == 200:
            break
        assert code == 200 or code == 404, (
            f'Failed to get VMI {name}: {vmi}')

        time.sleep(3)
        response = api_client._get(vmi_path)
        code = response.status_code
        vmi = response.json()
    assert datetime.now() < end_time, (
        f'Timed-out getting VMI {name}.')
    return vmi


def _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout):
    vmi = _get_vmi(endpoint, api_client, vm_name, wait_timeout)

    end_time = datetime.now() + timedelta(seconds=wait_timeout)
    ip = _find_ip_address_in_vmi(vmi)
    while datetime.now() < end_time:
        if ip != '':
            break

        time.sleep(3)
        vmi = _get_vmi(endpoint, api_client, vm_name, wait_timeout)
        ip = _find_ip_address_in_vmi(vmi)

    assert datetime.now() < end_time, (
        'Timed-out waiting for VM IP address.')
    return ip


@pytest.fixture(scope='module')
def backup_target_nfs(request, api_client):
    nfs_endpoint = request.config.getoption('--nfs-endpoint')

    spec = api_client.settings.BackupTargetSpec.NFS(nfs_endpoint)
    code, data = api_client.settings.update('backup-target', spec)
    assert 200 == code, (
        f'Failed to update backup target to NFS: {data}')


@pytest.fixture(scope='module')
def backup_target_s3(request, api_client):
    s3_endpoint = request.config.getoption('--s3-endpoint')
    bucket = request.config.getoption('--bucketName')
    region = request.config.getoption('--region')
    access_key_id = request.config.getoption('--accessKeyId')
    secret_access_key = request.config.getoption('--secretAccessKey')

    spec = api_client.settings.BackupTargetSpec.S3(bucket,
                                                   region,
                                                   access_key_id,
                                                   secret_access_key,
                                                   s3_endpoint)
    code, data = api_client.settings.update('backup-target', spec)
    assert 200 == code, (
        f'Failed to update backup target to S3: {data}')


@pytest.fixture(scope='class')
def vm_name(unique_name):
    return f'vm-{unique_name}'


@pytest.fixture(scope='class')
def image_display_name(unique_name):
    return f'image-{unique_name}'


@pytest.fixture(scope='class')
def restored_vm_name(unique_name):
    return f'restored-{unique_name}'


@pytest.fixture(scope='class')
def backup_name(unique_name):
    return f'backup-{unique_name}'


@pytest.fixture(scope='class')
def image(wait_timeout, api_client, image_display_name, need_cleanup):
    code, data = api_client.images.get(image_display_name)
    if 200 == code:
        yield data['metadata']['name']
    else:
        code, image = api_client.images.create_by_url(image_display_name, IMAGE_URL)
        assert 201 == code, (
            f'Failed to create image: {image}')
        image_name = image['metadata']['name']
        _wait_for_image_ready(wait_timeout, api_client, image_name)
        yield f'default/{image_name}'

    if need_cleanup:
        api_client.images.delete(image_name)


@pytest.fixture(scope='class')
def base_vm(api_client, image, vm_name,
            need_cleanup, ssh_keypair):
    image_name = image
    public_key, private_key = ssh_keypair

    cloud_init = f"""
    #cloud-config
    package_update: true
    packages:
      - qemu-guest-agent
    runcmd:
      - - systemctl
        - enable
        - --now
        - qemu-guest-agent.service
    ssh_keys:
      rsa_private: ''
      rsa_public: {public_key}
    password: 123456
    chpasswd:
      expire: false
    ssh_pwauth: true
    """
    cloud_init_obj = yaml.full_load(cloud_init)
    cloud_init_obj['ssh_keys']['rsa_private'] = private_key
    cloud_init = yaml.dump(cloud_init_obj)

    vm = api_client.vms.Spec(2, 4, 'VM for testing purposes.')
    vm.user_data = cloud_init
    vm.add_image('disk0', image_name)
    vm.guest_agent = True
    code, vm_data = api_client.vms.create(vm_name, vm)
    assert 201 == code, (
        f'Failed to create test VM: {vm_data}')
    api_client.vms.start(vm_name)

    yield vm_data
    if need_cleanup:
        api_client.vms.delete(vm_name)


@pytest.fixture(scope='class')
def vm_backups(endpoint, endpoint_ip, api_client,
               base_vm, wait_timeout, vm_name,
               backup_name, need_cleanup, host_shell,
               vm_shell, ssh_keypair):
    host_ip = endpoint_ip
    ip = _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout)
    _, private_key = ssh_keypair

    _wait_for_vm_ready(api_client, wait_timeout, vm_name)
    backups = []
    with host_shell.login(host_ip, jumphost=True) as host, \
         vm_shell.login(ipaddr=ip,
                        username=USERNAME,
                        password=PASSWORD,
                        pkey=private_key,
                        jumphost=host.client) as vm:
        for i in range(0, 5):
            current_backup_name = f'{backup_name}-{i}'

            _create_random_file_with_md5(vm, f'test-{i}')
            code, _ = api_client.vms.backup(vm_name, current_backup_name)
            assert 204 == code, (
                f'Failed to create backup {current_backup_name}: {code}')
            _wait_for_backup_ready(wait_timeout, api_client, current_backup_name)

            code, backup = api_client.backups.get(current_backup_name)
            assert 200 == code, (
                f'Failed to get backup {current_backup_name}: {backup}')
            backups.append(backup)

    yield backups
    if need_cleanup:
        for backup in backups:
            backup_name = backup['metadata']['name']
            code, _ = api_client.backups.get(backup_name)
            if code == 200:
                api_client.backups.delete(backup_name)


@pytest.mark.p0
@pytest.mark.backupnfs
def test_backup_target_nfs(api_client, backup_target_nfs):
    code, data = api_client.settings.backup_target_test_connection()
    assert 200 == code, (
        f'Failed to test backup target connection: {data}')


@pytest.mark.p0
@pytest.mark.backups3
def test_backup_target_s3(api_client, backup_target_s3):
    code, data = api_client.settings.backup_target_test_connection()
    assert 200 == code, (
        f'Failed to test backup target connection: {data}')


@pytest.mark.p0
@pytest.mark.backupnfs
class TestBackupRestoreNFS:
    def test_restore_with_new_vm(self, endpoint, api_client,
                                 vm_backups, wait_timeout, restored_vm_name,
                                 host_shell, vm_shell, need_cleanup,
                                 ssh_keypair, endpoint_ip):
        vm_name = restored_vm_name
        backup_name = vm_backups[1]['metadata']['name']
        spec = api_client.backups.RestoreSpec.for_new(vm_name)
        code, data = api_client.backups.restore(backup_name,
                                                spec)
        assert 201 == code, (
            f'Failed to restore backup with new VM, {data}')

        _, private_key = ssh_keypair
        _wait_for_vm_ready(api_client, wait_timeout, vm_name)
        ip = _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout)
        with host_shell.login(ipaddr=endpoint_ip, jumphost=True) as host, \
             vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-0') and
                      _check_file_integrity(vm, 'test-1'))
            assert intact, (
                'Restore failed, "test-0" file not found or md5 mismatch.')

        if need_cleanup:
            api_client.vms.delete(vm_name)

    def test_restore_replace_current_vm(self, endpoint, api_client,
                                        vm_backups, wait_timeout, host_shell,
                                        vm_shell, need_cleanup, ssh_keypair,
                                        endpoint_ip, vm_name):
        backup_name = vm_backups[1]['metadata']['name']
        spec = api_client.backups.RestoreSpec.for_existing(delete_volumes=True)

        _wait_for_vm_stop(api_client, wait_timeout, vm_name)
        code, data = api_client.backups.restore(backup_name,
                                                spec)
        assert 201 == code, (
            f'Failed to restore backup with current VM replaced, {data}')

        _, private_key = ssh_keypair
        _wait_for_vm_ready(api_client, wait_timeout, vm_name)
        ip = _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout)
        with host_shell.login(ipaddr=endpoint_ip, jumphost=True) as host, \
             vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-0') and
                      _check_file_integrity(vm, 'test-1'))
            assert intact, (
                'Restore failed, "test-0" file not found or md5 mismatch.')

        if need_cleanup:
            api_client.vms.delete(vm_name)


@pytest.mark.p0
@pytest.mark.backupnfs
class TestDeleteBackupNFS:
    def test_delete_first_backup(self, endpoint, api_client,
                                 vm_name, restored_vm_name, wait_timeout,
                                 vm_backups, ssh_keypair, need_cleanup,
                                 host_shell, vm_shell, endpoint_ip):
        backup_to_delete = vm_backups[0]['metadata']['name']
        code, data = api_client.backups.delete(backup_to_delete)
        assert 200 == code, (
            f'Failed to delete backup: {data}')

        _, private_key = ssh_keypair
        ip = _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, vm_name)
        host = host_shell.login(ipaddr=endpoint_ip, jumphost=True)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-1') and
                      _check_file_integrity(vm, 'test-2') and
                      _check_file_integrity(vm, 'test-3') and
                      _check_file_integrity(vm, 'test-4'))
            assert intact, (
                'Failed to check file integrity after deletion of first backup.')

        backup_to_restore = vm_backups[1]['metadata']['name']
        spec = api_client.backups.RestoreSpec.for_new(restored_vm_name)
        code, data = api_client.backups.restore(name=backup_to_restore,
                                                restore_spec=spec)
        assert 201 == code, (
            f'Failed to restore backup: {data}')

        ip = _wait_for_vm_ip(endpoint, api_client, restored_vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, restored_vm_name)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-0') and
                      _check_file_integrity(vm, 'test-1'))
            assert intact, (
                'Failed to check file integrity on restored new VM.')

        if need_cleanup:
            api_client.vms.delete(name=restored_vm_name)

    def test_delete_last_backup(self, endpoint, api_client,
                                vm_name, restored_vm_name, wait_timeout,
                                vm_backups, ssh_keypair, need_cleanup,
                                host_shell, vm_shell, endpoint_ip):
        backup_to_delete = vm_backups[4]['metadata']['name']
        code, data = api_client.backups.delete(backup_to_delete)
        assert 200 == code, (
            f'Failed to delete backup: {data}')

        _, private_key = ssh_keypair
        ip = _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, vm_name)
        host = host_shell.login(ipaddr=endpoint_ip, jumphost=True)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-1') and
                      _check_file_integrity(vm, 'test-2') and
                      _check_file_integrity(vm, 'test-3') and
                      _check_file_integrity(vm, 'test-4'))
            assert intact, (
                'Failed to check file integrity after deletion of last backup.')

        backup_to_restore = vm_backups[3]['metadata']['name']
        spec = api_client.backups.RestoreSpec.for_new(restored_vm_name)
        code, data = api_client.backups.restore(name=backup_to_restore,
                                                restore_spec=spec)
        assert 201 == code, (
            f'Failed to restore backup: {data}')

        ip = _wait_for_vm_ip(endpoint, api_client, restored_vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, restored_vm_name)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-0') and
                      _check_file_integrity(vm, 'test-1') and
                      _check_file_integrity(vm, 'test-2') and
                      _check_file_integrity(vm, 'test-3'))
            assert intact, (
                'Failed to check file integrity on restored new VM.')

        if need_cleanup:
            api_client.vms.delete(name=restored_vm_name)

    def test_delete_middle_backup(self, endpoint, api_client,
                                  vm_name, restored_vm_name, wait_timeout,
                                  vm_backups, ssh_keypair, need_cleanup,
                                  host_shell, vm_shell, endpoint_ip):
        backup_to_delete = vm_backups[2]['metadata']['name']
        code, data = api_client.backups.delete(backup_to_delete)
        assert 200 == code, (
            f'Failed to delete backup: {data}')

        _, private_key = ssh_keypair
        ip = _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, vm_name)
        host = host_shell.login(ipaddr=endpoint_ip, jumphost=True)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-1') and
                      _check_file_integrity(vm, 'test-2') and
                      _check_file_integrity(vm, 'test-3') and
                      _check_file_integrity(vm, 'test-4'))
            assert intact, (
                'Failed to check file integrity after deletion of middle backup.')

        backup_to_restore = vm_backups[1]['metadata']['name']
        spec = api_client.backups.RestoreSpec.for_new(restored_vm_name)
        code, data = api_client.backups.restore(name=backup_to_restore,
                                                restore_spec=spec)
        assert 201 == code, (
            f'Failed to restore backup: {data}')

        ip = _wait_for_vm_ip(endpoint, api_client, restored_vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, restored_vm_name)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-0') and
                      _check_file_integrity(vm, 'test-1'))
            assert intact, (
                'Failed to check file integrity on restored new VM.')

        if need_cleanup:
            api_client.vms.delete(name=restored_vm_name)


@pytest.mark.p0
@pytest.mark.backups3
class TestBackupRestoreS3:
    def test_restore_with_new_vm(self, endpoint, api_client,
                                 vm_backups, wait_timeout, restored_vm_name,
                                 host_shell, vm_shell, need_cleanup,
                                 ssh_keypair, endpoint_ip):
        vm_name = restored_vm_name
        backup_name = vm_backups[1]['metadata']['name']
        spec = api_client.backups.RestoreSpec.for_new(vm_name)
        code, data = api_client.backups.restore(backup_name,
                                                spec)
        assert 201 == code, (
            f'Failed to restore backup with new VM, {data}')

        _, private_key = ssh_keypair
        _wait_for_vm_ready(api_client, wait_timeout, vm_name)
        ip = _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout)
        with host_shell.login(ipaddr=endpoint_ip, jumphost=True) as host, \
             vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-0') and
                      _check_file_integrity(vm, 'test-1'))
            assert intact, (
                'Restore failed, "test-0" file not found or md5 mismatch.')

        if need_cleanup:
            api_client.vms.delete(vm_name)

    def test_restore_replace_current_vm(self, endpoint, api_client,
                                        vm_backups, wait_timeout, host_shell,
                                        vm_shell, need_cleanup, ssh_keypair,
                                        endpoint_ip, vm_name):
        backup_name = vm_backups[1]['metadata']['name']
        spec = api_client.backups.RestoreSpec.for_existing(delete_volumes=True)

        _wait_for_vm_stop(api_client, wait_timeout, vm_name)
        code, data = api_client.backups.restore(backup_name,
                                                spec)
        assert 201 == code, (
            f'Failed to restore backup with current VM replaced, {data}')

        _, private_key = ssh_keypair
        _wait_for_vm_ready(api_client, wait_timeout, vm_name)
        ip = _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout)
        with host_shell.login(ipaddr=endpoint_ip, jumphost=True) as host, \
             vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-0') and
                      _check_file_integrity(vm, 'test-1'))
            assert intact, (
                'Restore failed, "test-0" file not found or md5 mismatch.')

        if need_cleanup:
            api_client.vms.delete(vm_name)


@pytest.mark.p0
@pytest.mark.backups3
class TestDeleteBackupS3:
    def test_delete_first_backup(self, endpoint, api_client,
                                 vm_name, restored_vm_name, wait_timeout,
                                 vm_backups, ssh_keypair, need_cleanup,
                                 host_shell, vm_shell, endpoint_ip):
        backup_to_delete = vm_backups[0]['metadata']['name']
        code, data = api_client.backups.delete(backup_to_delete)
        assert 200 == code, (
            f'Failed to delete backup: {data}')

        _, private_key = ssh_keypair
        ip = _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, vm_name)
        host = host_shell.login(ipaddr=endpoint_ip, jumphost=True)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-1') and
                      _check_file_integrity(vm, 'test-2') and
                      _check_file_integrity(vm, 'test-3') and
                      _check_file_integrity(vm, 'test-4'))
            assert intact, (
                'Failed to check file integrity after deletion of first backup.')

        backup_to_restore = vm_backups[1]['metadata']['name']
        spec = api_client.backups.RestoreSpec.for_new(restored_vm_name)
        code, data = api_client.backups.restore(name=backup_to_restore,
                                                restore_spec=spec)
        assert 201 == code, (
            f'Failed to restore backup: {data}')

        ip = _wait_for_vm_ip(endpoint, api_client, restored_vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, restored_vm_name)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-0') and
                      _check_file_integrity(vm, 'test-1'))
            assert intact, (
                'Failed to check file integrity on restored new VM.')

        if need_cleanup:
            api_client.vms.delete(name=restored_vm_name)

    def test_delete_last_backup(self, endpoint, api_client,
                                vm_name, restored_vm_name, wait_timeout,
                                vm_backups, ssh_keypair, need_cleanup,
                                host_shell, vm_shell, endpoint_ip):
        backup_to_delete = vm_backups[4]['metadata']['name']
        code, data = api_client.backups.delete(backup_to_delete)
        assert 200 == code, (
            f'Failed to delete backup: {data}')

        _, private_key = ssh_keypair
        ip = _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, vm_name)
        host = host_shell.login(ipaddr=endpoint_ip, jumphost=True)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-1') and
                      _check_file_integrity(vm, 'test-2') and
                      _check_file_integrity(vm, 'test-3') and
                      _check_file_integrity(vm, 'test-4'))
            assert intact, (
                'Failed to check file integrity after deletion of last backup.')

        backup_to_restore = vm_backups[3]['metadata']['name']
        spec = api_client.backups.RestoreSpec.for_new(restored_vm_name)
        code, data = api_client.backups.restore(name=backup_to_restore,
                                                restore_spec=spec)
        assert 201 == code, (
            f'Failed to restore backup: {data}')

        ip = _wait_for_vm_ip(endpoint, api_client, restored_vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, restored_vm_name)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-0') and
                      _check_file_integrity(vm, 'test-1') and
                      _check_file_integrity(vm, 'test-2') and
                      _check_file_integrity(vm, 'test-3'))
            assert intact, (
                'Failed to check file integrity on restored new VM.')

        if need_cleanup:
            api_client.vms.delete(name=restored_vm_name)

    def test_delete_middle_backup(self, endpoint, api_client,
                                  vm_name, restored_vm_name, wait_timeout,
                                  vm_backups, ssh_keypair, need_cleanup,
                                  host_shell, vm_shell, endpoint_ip):
        backup_to_delete = vm_backups[2]['metadata']['name']
        code, data = api_client.backups.delete(backup_to_delete)
        assert 200 == code, (
            f'Failed to delete backup: {data}')

        _, private_key = ssh_keypair
        ip = _wait_for_vm_ip(endpoint, api_client, vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, vm_name)
        host = host_shell.login(ipaddr=endpoint_ip, jumphost=True)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-1') and
                      _check_file_integrity(vm, 'test-2') and
                      _check_file_integrity(vm, 'test-3') and
                      _check_file_integrity(vm, 'test-4'))
            assert intact, (
                'Failed to check file integrity after deletion of middle backup.')

        backup_to_restore = vm_backups[1]['metadata']['name']
        spec = api_client.backups.RestoreSpec.for_new(restored_vm_name)
        code, data = api_client.backups.restore(name=backup_to_restore,
                                                restore_spec=spec)
        assert 201 == code, (
            f'Failed to restore backup: {data}')

        ip = _wait_for_vm_ip(endpoint, api_client, restored_vm_name, wait_timeout)
        _wait_for_vm_ready(api_client, wait_timeout, restored_vm_name)
        with vm_shell.login(ipaddr=ip,
                            username=USERNAME,
                            password=PASSWORD,
                            pkey=private_key,
                            jumphost=host.client) as vm:
            intact = (_check_file_integrity(vm, 'test-0') and
                      _check_file_integrity(vm, 'test-1'))
            assert intact, (
                'Failed to check file integrity on restored new VM.')

        if need_cleanup:
            api_client.vms.delete(name=restored_vm_name)
