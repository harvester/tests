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
from time import sleep
from datetime import datetime, timedelta

import yaml
import pytest
from paramiko.ssh_exception import ChannelException

pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_client',
    'harvester_e2e_tests.fixtures.images',
    'harvester_e2e_tests.fixtures.virtualmachines'
]


@pytest.fixture(scope="module")
def conflict_retries():
    # This might be able to moved to config options in need.
    return 5


@pytest.fixture(scope="module")
def image(api_client, unique_name, wait_timeout, image_opensuse):
    unique_image_id = f'image-{unique_name}'
    code, data = api_client.images.create_by_url(
        unique_image_id, image_opensuse.url, display_name=f"{unique_name}-{image_opensuse.name}"
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
               user=image_opensuse.ssh_user)

    code, data = api_client.images.delete(unique_image_id)


@pytest.fixture(scope='module')
def NFS_config(request):
    nfs_endpoint = request.config.getoption('--nfs-endpoint')

    assert nfs_endpoint, f"NFS endpoint not configured: {nfs_endpoint}"
    assert nfs_endpoint.startswith("nfs://"), (
        f"NFS endpoint should starts with `nfs://`, not {nfs_endpoint}"
    )

    return ("NFS", dict(endpoint=nfs_endpoint))


@pytest.fixture(scope='module')
def S3_config(request):
    config = {
        "bucket": request.config.getoption('--bucketName'),
        "region": request.config.getoption('--region'),
        "access_id": request.config.getoption('--accessKeyId'),
        "access_secret": request.config.getoption('--secretAccessKey')
    }

    empty_options = ', '.join(k for k, v in config.items() if not v)
    assert not empty_options, (
        f"S3 configuration missing, `{empty_options}` should not be empty."
    )

    config['endpoint'] = request.config.getoption('--s3-endpoint')

    return ("S3", config)


@pytest.fixture(scope="class")
def backup_config(request):
    return request.getfixturevalue(f"{request.param}_config")


@pytest.fixture(scope="class")
def config_backup_target(api_client, conflict_retries, backup_config):
    backup_type, config = backup_config
    code, data = api_client.settings.get('backup-target')
    origin_spec = api_client.settings.BackupTargetSpec.from_dict(data)

    spec = getattr(api_client.settings.BackupTargetSpec, backup_type)(**config)
    # ???: when switching S3 -> NFS, update backup-target will easily hit resource conflict
    # so we would need retries to apply the change.
    for _ in range(conflict_retries):
        code, data = api_client.settings.update('backup-target', spec)
        if 409 == code and "Conflict" == data['reason']:
            sleep(3)
        else:
            break
    else:
        raise AssertionError(
            f"Unable to update backup-target after {conflict_retries} retried."
            f"API Status({code}): {data}"
        )
    assert 200 == code, (
        f'Failed to update backup target to {backup_type} with {config}\n'
        f"API Status({code}): {data}"
    )

    yield spec

    # restore to original backup-target and remove backups not belong to it
    code, data = api_client.settings.update('backup-target', origin_spec)
    code, data = api_client.backups.get()
    assert 200 == code, "Failed to list backups"

    for backup in data['data']:
        endpoint = backup['status']['backupTarget'].get('endpoint')
        if endpoint != origin_spec.value.get('endpoint'):
            api_client.backups.delete(backup['metadata']['name'])


@pytest.fixture(scope="class")
def base_vm_with_data(
    api_client, host_shell, vm_shell, ssh_keypair, wait_timeout, unique_name, image, backup_config
):
    unique_vm_name = f"{datetime.now().strftime('%m%S%f')}-{unique_name}"
    cpu, mem = 1, 2
    pub_key, pri_key = ssh_keypair
    vm_spec = api_client.vms.Spec(cpu, mem)
    vm_spec.add_image("disk-0", image['id'])

    userdata = yaml.safe_load(vm_spec.user_data)
    userdata['ssh_authorized_keys'] = [pub_key]
    userdata['password'] = 'password'
    userdata['chpasswd'] = dict(expire=False)
    userdata['sshpwauth'] = True
    vm_spec.user_data = yaml.dump(userdata)
    code, data = api_client.vms.create(unique_vm_name, vm_spec)

    # Check VM started and get IPs (vm and host)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_vm_name)
        if 200 == code:
            phase = data.get('status', {}).get('phase')
            conds = data.get('status', {}).get('conditions', [{}])
            if ("Running" == phase
               and "AgentConnected" == conds[-1].get('type')
               and data['status'].get('interfaces')):
                break
        sleep(3)
    else:
        raise AssertionError(
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
    vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                 if iface['name'] == 'default')
    code, data = api_client.hosts.get(data['status']['nodeName'])
    host_ip = next(addr['address'] for addr in data['status']['addresses']
                   if addr['type'] == 'InternalIP')

    # Log into VM to make some data
    with host_shell.login(host_ip, jumphost=True) as h:
        vm_sh = vm_shell(image['user'], pkey=pri_key)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            try:
                vm_sh.connect(vm_ip, jumphost=h.client)
            except ChannelException as e:
                login_ex = e
                sleep(3)
            else:
                break
        else:
            raise AssertionError(f"Unable to login to VM {unique_vm_name}") from login_ex

        with vm_sh as sh:
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                out, err = sh.exec_command('cloud-init status')
                if 'done' in out:
                    break
                sleep(3)
            else:
                raise AssertionError(
                    f"VM {unique_vm_name} Started {wait_timeout} seconds"
                    f", but cloud-init still in {out}"
                )
            out, err = sh.exec_command(f'echo {unique_vm_name!r} > ~/vmname')
            assert not err, (out, err)
            sh.exec_command('sync')

    yield {
        "name": unique_vm_name,
        "ssh_user": image['user'],
        "data": dict(path="~/vmname", content=f'{unique_vm_name}')
    }

    # remove backups link to the VM and is ready
    code, data = api_client.backups.get()
    for backup in data['data']:
        if (backup['status'].get('readyToUse') and
                unique_vm_name == backup['spec']['source']['name']):
            api_client.backups.delete(backup['metadata']['name'])

    # remove created VM
    code, data = api_client.vms.get(unique_vm_name)
    vm_spec = api_client.vms.Spec.from_dict(data)

    api_client.vms.delete(unique_vm_name)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_vm_name)
        if 404 == code:
            break
        sleep(3)

    for vol in vm_spec.volumes:
        vol_name = vol['volume']['persistentVolumeClaim']['claimName']
        api_client.volumes.delete(vol_name)


@pytest.mark.p0
@pytest.mark.backup_target
@pytest.mark.parametrize(
    "backup_config", [
        pytest.param("S3", marks=pytest.mark.S3),
        pytest.param("NFS", marks=pytest.mark.NFS)
    ],
    indirect=True)
class TestBackupRestore:

    @pytest.mark.dependency()
    def test_connection(self, api_client, backup_config, config_backup_target):
        code, data = api_client.settings.backup_target_test_connection()
        assert 200 == code, f'Failed to test backup target connection: {data}'

    @pytest.mark.dependency(depends=["TestBackupRestore::test_connection"], param=True)
    def tests_backup_vm(self, api_client, wait_timeout, backup_config, base_vm_with_data):
        unique_vm_name = base_vm_with_data['name']

        # Create backup with the name as VM's name
        code, data = api_client.vms.backup(unique_vm_name, unique_vm_name)
        assert 204 == code, (code, data)
        # Check backup is ready
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, backup = api_client.backups.get(unique_vm_name)
            if 200 == code and backup.get('status', {}).get('readyToUse'):
                break
            sleep(3)
        else:
            raise AssertionError(
                f'Timed-out waiting for the backup \'{unique_vm_name}\' to be ready.'
            )

    @pytest.mark.dependency(depends=["TestBackupRestore::tests_backup_vm"], param=True)
    def test_restore_with_new_vm(
        self, api_client, host_shell, vm_shell, ssh_keypair, wait_timeout,
        backup_config, base_vm_with_data
    ):
        unique_vm_name, backup_data = base_vm_with_data['name'], base_vm_with_data['data']
        pub_key, pri_key = ssh_keypair

        restored_vm_name = f"nfs-restore-{unique_vm_name}"
        spec = api_client.backups.RestoreSpec.for_new(restored_vm_name)
        code, data = api_client.backups.restore(unique_vm_name, spec)
        assert 201 == code, (code, data)

        # Check VM Started then get IPs (vm and host)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(restored_vm_name)
            if 200 == code:
                phase = data.get('status', {}).get('phase')
                conds = data.get('status', {}).get('conditions', [{}])
                if ("Running" == phase
                   and "AgentConnected" == conds[-1].get('type')
                   and data['status'].get('interfaces')):
                    break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Start VM({restored_vm_name}) with errors:\n"
                f"Status: {data.get('status')}\n"
                f"API Status({code}): {data}"
            )
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        # Login to the new VM and check data is existing
        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(base_vm_with_data['ssh_user'], pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {restored_vm_name}") from login_ex

            with vm_sh as sh:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    out, err = sh.exec_command('cloud-init status')
                    if 'done' in out:
                        break
                    sleep(3)
                else:
                    raise AssertionError(
                        f"VM {restored_vm_name} Started {wait_timeout} seconds"
                        f", but cloud-init still in {out}"
                    )

                out, err = sh.exec_command(f"cat {backup_data['path']}")
            assert backup_data['content'] in out, (
                f"cloud-init writefile failed\n"
                f"Executed stdout: {out}\n"
                f"Executed stderr: {err}"
            )

        # teardown: delete restored vm and volumes
        code, data = api_client.vms.get(restored_vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        api_client.vms.delete(restored_vm_name)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(restored_vm_name)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Delete VM({restored_vm_name}) with errors:\n"
                f"Status({code}): {data}"
            )
        for vol in vm_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)

    @pytest.mark.dependency(depends=["TestBackupRestore::tests_backup_vm"], param=True)
    def test_restore_replace_and_delete_vols(
        self, api_client, host_shell, vm_shell, ssh_keypair, wait_timeout,
        backup_config, base_vm_with_data
    ):
        unique_vm_name, backup_data = base_vm_with_data['name'], base_vm_with_data['data']
        pub_key, pri_key = ssh_keypair

        # Stop the VM
        code, data = api_client.vms.stop(unique_vm_name)
        assert 204 == code, "`Stop` return unexpected status code"
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Stop VM({unique_vm_name}) with errors:\n"
                f"Status({code}): {data}"
            )

        spec = api_client.backups.RestoreSpec.for_existing(delete_volumes=True)
        code, data = api_client.backups.restore(unique_vm_name, spec)
        assert 201 == code, f'Failed to restore backup with current VM replaced, {data}'

        # Check VM Started then get IPs (vm and host)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if 200 == code:
                phase = data.get('status', {}).get('phase')
                conds = data.get('status', {}).get('conditions', [{}])
                if ("Running" == phase
                   and "AgentConnected" == conds[-1].get('type')
                   and data['status'].get('interfaces')):
                    break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Start VM({unique_vm_name}) with errors:\n"
                f"Status: {data.get('status')}\n"
                f"API Status({code}): {data}"
            )
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        # Login to the new VM and check data is existing
        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(base_vm_with_data['ssh_user'], pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {unique_vm_name}") from login_ex

            with vm_sh as sh:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    out, err = sh.exec_command('cloud-init status')
                    if 'done' in out:
                        break
                    sleep(3)
                else:
                    raise AssertionError(
                        f"VM {unique_vm_name} Started {wait_timeout} seconds"
                        f", but cloud-init still in {out}"
                    )

                out, err = sh.exec_command(f"cat {backup_data['path']}")
            assert backup_data['content'] in out, (
                f"cloud-init writefile failed\n"
                f"Executed stdout: {out}\n"
                f"Executed stderr: {err}"
            )


@pytest.mark.p1
@pytest.mark.backup_target
@pytest.mark.parametrize(
    "backup_config", [
        pytest.param("S3", marks=pytest.mark.S3),
        pytest.param("NFS", marks=pytest.mark.NFS)
    ],
    indirect=True)
class TestMultipleBackupRestore:
    @pytest.mark.dependency()
    def test_backup_multiple(
        self, api_client, wait_timeout, host_shell, vm_shell, ssh_keypair,
        backup_config, config_backup_target, base_vm_with_data
    ):
        def write_data(content):
            pub_key, pri_key = ssh_keypair
            # Log into VM to make some data
            with host_shell.login(host_ip, jumphost=True) as h:
                vm_sh = vm_shell(base_vm_with_data['ssh_user'], pkey=pri_key)
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    try:
                        vm_sh.connect(vm_ip, jumphost=h.client)
                    except ChannelException as e:
                        login_ex = e
                        sleep(3)
                    else:
                        break
                else:
                    raise AssertionError(f"Unable to login to VM {unique_vm_name}") from login_ex

                with vm_sh as sh:
                    endtime = datetime.now() + timedelta(seconds=wait_timeout)
                    while endtime > datetime.now():
                        out, err = sh.exec_command('cloud-init status')
                        if 'done' in out:
                            break
                        sleep(3)
                    else:
                        raise AssertionError(
                            f"VM {unique_vm_name} Started {wait_timeout} seconds"
                            f", but cloud-init still in {out}"
                        )
                    out, err = sh.exec_command(f'echo {content!r} >> ~/vmname')
                    assert not err, (out, err)
                    sh.exec_command('sync')

        def create_backup(vm_name, backup_name):
            code, data = api_client.vms.backup(vm_name, backup_name)
            assert 204 == code, (code, data)
            # Check backup is ready
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                code, backup = api_client.backups.get(backup_name)
                if 200 == code and backup.get('status', {}).get('readyToUse'):
                    break
                sleep(3)
            else:
                raise AssertionError(
                    f'Timed-out waiting for the backup \'{backup_name}\' to be ready.'
                )

        unique_vm_name = base_vm_with_data['name']
        # Check VM started and get IPs (vm and host)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if 200 == code:
                phase = data.get('status', {}).get('phase')
                conds = data.get('status', {}).get('conditions', [{}])
                if ("Running" == phase
                   and "AgentConnected" == conds[-1].get('type')
                   and data['status'].get('interfaces')):
                    break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Start VM({unique_vm_name}) with errors:\n"
                f"Status: {data.get('status')}\n"
                f"API Status({code}): {data}"
            )
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        content = ""
        # Create multiple backups
        for idx in range(0, 5):
            backup_name = f"{idx}-{unique_vm_name}"
            write_data(backup_name)
            create_backup(unique_vm_name, backup_name)
            content += f"{backup_name}\n"
            base_vm_with_data['data'].setdefault('backups', []).append((backup_name, content))

    @pytest.mark.dependency(
        depends=["TestMultipleBackupRestore::test_backup_multiple"], param=True
    )
    def test_delete_first_backup(
        self, api_client, host_shell, vm_shell, ssh_keypair, wait_timeout,
        backup_config, config_backup_target, base_vm_with_data
    ):
        unique_vm_name, backup_data = base_vm_with_data['name'], base_vm_with_data['data']
        pub_key, pri_key = ssh_keypair

        backups = backup_data['backups']
        (first_backup, content), *backup_data['backups'] = backups
        latest_backup = backups[-1][0]

        # Delete first backup
        code, data = api_client.backups.delete(first_backup)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.backups.get(first_backup)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to delete backup {first_backup}\n"
                f"API Status({code}): {data}"
            )

        # Stop the VM
        code, data = api_client.vms.stop(unique_vm_name)
        assert 204 == code, "`Stop` return unexpected status code"
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Stop VM({unique_vm_name}) with errors:\n"
                f"Status({code}): {data}"
            )

        spec = api_client.backups.RestoreSpec.for_existing(delete_volumes=True)
        code, data = api_client.backups.restore(latest_backup, spec)
        assert 201 == code, f'Failed to restore backup with current VM replaced, {data}'

        # Check VM Started then get IPs (vm and host)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if 200 == code:
                phase = data.get('status', {}).get('phase')
                conds = data.get('status', {}).get('conditions', [{}])
                if ("Running" == phase
                   and "AgentConnected" == conds[-1].get('type')
                   and data['status'].get('interfaces')):
                    break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Start VM({unique_vm_name}) with errors:\n"
                f"Status: {data.get('status')}\n"
                f"API Status({code}): {data}"
            )
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        # Login to the new VM and check data is existing
        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(base_vm_with_data['ssh_user'], pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {unique_vm_name}") from login_ex

            with vm_sh as sh:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    out, err = sh.exec_command('cloud-init status')
                    if 'done' in out:
                        break
                    sleep(3)
                else:
                    raise AssertionError(
                        f"VM {unique_vm_name} Started {wait_timeout} seconds"
                        f", but cloud-init still in {out}"
                    )

                out, err = sh.exec_command(f"cat {backup_data['path']}")
            assert content in out, (
                f"cloud-init writefile failed\n"
                f"Executed stdout: {out}\n"
                f"Executed stderr: {err}"
            )

    @pytest.mark.dependency(
        depends=["TestMultipleBackupRestore::test_backup_multiple"], param=True
    )
    def test_delete_last_backup(
        self, api_client, host_shell, vm_shell, ssh_keypair, wait_timeout,
        backup_config, config_backup_target, base_vm_with_data
    ):
        unique_vm_name, backup_data = base_vm_with_data['name'], base_vm_with_data['data']
        pub_key, pri_key = ssh_keypair

        *backups, (latest_backup, content), (last_backup, _) = backup_data['backups']
        backup_data['backups'] = backup_data['backups'][:-1]

        # Delete first backup
        code, data = api_client.backups.delete(last_backup)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.backups.get(last_backup)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to delete backup {last_backup}\n"
                f"API Status({code}): {data}"
            )

        # Stop the VM
        code, data = api_client.vms.stop(unique_vm_name)
        assert 204 == code, "`Stop` return unexpected status code"
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Stop VM({unique_vm_name}) with errors:\n"
                f"Status({code}): {data}"
            )

        spec = api_client.backups.RestoreSpec.for_existing(delete_volumes=True)
        code, data = api_client.backups.restore(latest_backup, spec)
        assert 201 == code, f'Failed to restore backup with current VM replaced, {data}'

        # Check VM Started then get IPs (vm and host)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if 200 == code:
                phase = data.get('status', {}).get('phase')
                conds = data.get('status', {}).get('conditions', [{}])
                if ("Running" == phase
                   and "AgentConnected" == conds[-1].get('type')
                   and data['status'].get('interfaces')):
                    break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Start VM({unique_vm_name}) with errors:\n"
                f"Status: {data.get('status')}\n"
                f"API Status({code}): {data}"
            )
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        # Login to the new VM and check data is existing
        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(base_vm_with_data['ssh_user'], pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {unique_vm_name}") from login_ex

            with vm_sh as sh:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    out, err = sh.exec_command('cloud-init status')
                    if 'done' in out:
                        break
                    sleep(3)
                else:
                    raise AssertionError(
                        f"VM {unique_vm_name} Started {wait_timeout} seconds"
                        f", but cloud-init still in {out}"
                    )

                out, err = sh.exec_command(f"cat {backup_data['path']}")
            assert content in out, (
                f"cloud-init writefile failed\n"
                f"Executed stdout: {out}\n"
                f"Executed stderr: {err}"
            )

    @pytest.mark.dependency(
        depends=["TestMultipleBackupRestore::test_backup_multiple"], param=True
    )
    def test_delete_middle_backup(
        self, api_client, host_shell, vm_shell, ssh_keypair, wait_timeout,
        backup_config, config_backup_target, base_vm_with_data
    ):
        unique_vm_name, backup_data = base_vm_with_data['name'], base_vm_with_data['data']
        pub_key, pri_key = ssh_keypair

        *backups, (middle_backup, _), (latest_backup, content) = backup_data['backups']
        backup_data['backups'] = backups + [(latest_backup, content)]

        # Delete second last backup
        code, data = api_client.backups.delete(middle_backup)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.backups.get(middle_backup)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to delete backup {middle_backup}\n"
                f"API Status({code}): {data}"
            )

        # Stop the VM
        code, data = api_client.vms.stop(unique_vm_name)
        assert 204 == code, "`Stop` return unexpected status code"
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Stop VM({unique_vm_name}) with errors:\n"
                f"Status({code}): {data}"
            )

        spec = api_client.backups.RestoreSpec.for_existing(delete_volumes=True)
        code, data = api_client.backups.restore(latest_backup, spec)
        assert 201 == code, f'Failed to restore backup with current VM replaced, {data}'

        # Check VM Started then get IPs (vm and host)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if 200 == code:
                phase = data.get('status', {}).get('phase')
                conds = data.get('status', {}).get('conditions', [{}])
                if ("Running" == phase
                   and "AgentConnected" == conds[-1].get('type')
                   and data['status'].get('interfaces')):
                    break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Start VM({unique_vm_name}) with errors:\n"
                f"Status: {data.get('status')}\n"
                f"API Status({code}): {data}"
            )
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        # Login to the new VM and check data is existing
        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(base_vm_with_data['ssh_user'], pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {unique_vm_name}") from login_ex

            with vm_sh as sh:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    out, err = sh.exec_command('cloud-init status')
                    if 'done' in out:
                        break
                    sleep(3)
                else:
                    raise AssertionError(
                        f"VM {unique_vm_name} Started {wait_timeout} seconds"
                        f", but cloud-init still in {out}"
                    )

                out, err = sh.exec_command(f"cat {backup_data['path']}")
            assert content in out, (
                f"cloud-init writefile failed\n"
                f"Executed stdout: {out}\n"
                f"Executed stderr: {err}"
            )
