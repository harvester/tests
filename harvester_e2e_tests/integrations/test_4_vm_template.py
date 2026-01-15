from time import sleep
from datetime import datetime, timedelta

import pytest
import yaml


@pytest.fixture(scope="module")
def image(api_client, image_opensuse, unique_name, wait_timeout):
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


@pytest.fixture(scope="class")
def stopped_vm(api_client, ssh_keypair, wait_timeout, image, unique_name):
    unique_name = f"stopped-{datetime.now().strftime('%m%S%f')}-{unique_name}"
    cpu, mem = 1, 2
    pub_key, pri_key = ssh_keypair
    vm_spec = api_client.vms.Spec(cpu, mem)
    vm_spec.add_image("disk-0", image['id'])
    vm_spec.run_strategy = "Halted"

    userdata = yaml.safe_load(vm_spec.user_data)
    userdata['ssh_authorized_keys'] = [pub_key]
    vm_spec.user_data = yaml.dump(userdata)

    code, data = api_client.vms.create(unique_name, vm_spec)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get(unique_name)
        if "Stopped" == data.get('status', {}).get('printableStatus'):
            break
        sleep(1)

    yield unique_name, image['user']

    code, data = api_client.vms.get(unique_name)
    vm_spec = api_client.vms.Spec.from_dict(data)

    api_client.vms.delete(unique_name)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_name)
        if 404 == code:
            break
        sleep(3)

    for vol in vm_spec.volumes:
        vol_name = vol['volume']['persistentVolumeClaim']['claimName']
        api_client.volumes.delete(vol_name)


@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.templates
@pytest.mark.virtualmachines
class TestVMTemplate:
    def test_create_template_with_data(
        self, api_client, vm_shell_from_host, vm_checker, ssh_keypair, wait_timeout, stopped_vm
    ):
        """ ref: https://github.com/harvester/tests/issues/1194
        Steps:
            1. Create VM and write some data
            2. Create new template and keep data from the VM
            3. Create new VM from the template
            4. Check data consitency
        Expected result:
            - VM should created and operate normally
            - Template should created successfully
            - New VM should able to be created and operate normally
            - Data in new VM should consistent with old one
        """

        unique_name, ssh_user = stopped_vm
        pub_key, pri_key = ssh_keypair

        code, data = api_client.vms.start(unique_name)
        assert 204 == code, (code, data)
        vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(unique_name, ["default"])
        assert vm_got_ips, (
            f"Failed to Start VM({unique_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

        # Login to VM and write some data
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')
        with vm_shell_from_host(host_ip, vm_ip, ssh_user, pkey=pri_key) as sh:
            cloud_inited, (out, err) = vm_checker.wait_cloudinit_done(sh)
            assert cloud_inited, (
                f"VM {unique_name} Started {vm_checker.wait_timeout} seconds"
                f", but cloud-init still in {out}"
            )
            out, err = sh.exec_command(
                "dd if=/dev/urandom of=./generate_file bs=1M count=512; sync"
            )
            assert not out, (out, err)
            vm1_md5, err = sh.exec_command(
                "md5sum ./generate_file > ./generate_file.md5; cat ./generate_file.md5; sync"
            )
            assert not err, (vm1_md5, err)

        # generate VM template with data
        code, data = api_client.vms.create_template(unique_name, unique_name, keep_data=True)
        assert 204 == code, (code, data)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            try:
                code, data = api_client.templates.get(unique_name)
                assert 200 == code, (code, data)
                ns, name = data['spec']['defaultVersionId'].split('/')
            except (AssertionError, ValueError):
                # ValueError: version is not created yet, so `defaultVersionId` will be empty
                pass
            else:
                code, data = api_client.templates.get_version(name, ns)
                conds = data.get('status', {}).get('conditions', [])
                if conds and all('True' == c['status'] for c in conds):
                    tmpl_spec = api_client.templates.Spec.from_dict(data)
                    break
            sleep(5)
        else:
            raise AssertionError(
                "Failed to create template with status:\n"
                f"{data.get('status')}\n"
                f"API Status({code}): {data}"
            )

        # Create new VM from the template
        tmpl_vm_name = f"tmpl-{unique_name}"
        code, data = api_client.vms.create(tmpl_vm_name, tmpl_spec)
        assert 201 == code, (code, data)

        vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(tmpl_vm_name, ["default"])
        assert vm_got_ips, (
            f"Failed to Start VM({tmpl_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

        # Login to VM and check the data is consistent
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')
        with vm_shell_from_host(host_ip, vm_ip, ssh_user, pkey=pri_key) as sh:
            cloud_inited, (out, err) = vm_checker.wait_cloudinit_done(sh)
            assert cloud_inited, (
                f"VM {tmpl_vm_name} Started {vm_checker.wait_timeout} seconds"
                f", but cloud-init still in {out}"
            )
            out, err = sh.exec_command("md5sum -c ./generate_file.md5")
            assert not err, (out, err)
            vm2_md5, err = sh.exec_command("cat ./generate_file.md5")
            assert not err, (vm2_md5, err)
            assert vm1_md5 == vm2_md5

        # teardown
        api_client.vms.delete(tmpl_vm_name)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(tmpl_vm_name)
            if 404 == code:
                break
            sleep(3)

        for vol in tmpl_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)

        code, data = api_client.templates.delete(unique_name)
        assert 200 == code, (code, data)
