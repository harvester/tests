import yaml
from datetime import datetime, timedelta
from time import sleep

from paramiko.ssh_exception import ChannelException
import pytest


pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.virtualmachines"
]


def unique_name(name):
    return f"{datetime.now().strftime('%m%S%f')}-{name}"


@pytest.fixture(scope="class")
def sourcevm_name():
    return unique_name("source-vm")


@pytest.fixture(scope="class")
def restored_from_snapshot_name():
    return unique_name("vm-from-snapshot")


@pytest.fixture(scope="class")
def restored_from_snapshot_name_2():
    return unique_name("vm-from-snapshot-2")


@pytest.fixture(scope="class")
def vm_snapshot_name():
    return "vm-snapshot"


@pytest.fixture(scope="class")
def vm_snapshot_2_name():
    return "vm-snapshot-2"


@pytest.fixture(scope="module")
def image(api_client, image_opensuse, wait_timeout):
    unique_image_id = unique_name("image")
    display_name = f"{unique_image_id}-{image_opensuse.name}"
    code, data = api_client.images.create_by_url(unique_image_id,
                                                 image_opensuse.url,
                                                 display_name=display_name)

    assert 201 == code, (code, data)

    deadline = datetime.now() + timedelta(seconds=wait_timeout)
    while deadline > datetime.now():
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


def create_vm(name, api_client, ssh_keypair, image, timeout_secs):
    cpu = 1
    mem = 2
    pubkey, _ = ssh_keypair

    vm_spec = api_client.vms.Spec(cpu, mem)
    vm_spec.add_image("disk-0", image["id"])

    userdata = yaml.safe_load(vm_spec.user_data)
    userdata["ssh_authorized_keys"] = [pubkey]
    vm_spec.user_data = yaml.dump(userdata)

    _, data = api_client.vms.create(name, vm_spec)
    deadline = datetime.now() + timedelta(seconds=timeout_secs)
    while deadline > datetime.now():
        _, data = api_client.vms.get(name)
        if "Running" == data.get("status", {}).get("printableStatus"):
            break
        sleep(1)
    else:
        raise AssertionError(f"timed out waiting for {name} to transition to Running")

    return name, image["user"]


def delete_vm(name, api_client, timeout_secs):
    code, data = api_client.vms.get(name)
    if code == 404:
        return

    vm_spec = api_client.vms.Spec.from_dict(data)

    api_client.vms.delete(name)
    deadline = datetime.now() + timedelta(seconds=timeout_secs)
    while deadline > datetime.now():
        code, data = api_client.vms.get_status(name)
        if 404 == code:
            break
        sleep(3)

    for vol in vm_spec.volumes:
        vol_name = vol["volume"]["persistentVolumeClaim"]["claimName"]
        api_client.volumes.delete(vol_name)


def start_vm(name, api_client, timeout_secs):
    _, data = api_client.vms.start(name)
    deadline = datetime.now() + timedelta(seconds=timeout_secs)
    while deadline > datetime.now():
        _, data = api_client.vms.get(name)
        status = data.get("status", {}).get("printableStatus")
        if "Running" == status:
            return
        sleep(1)

    raise AssertionError(f"timed out trying to start {name}")


def stop_vm(name, api_client, timeout_secs):
    _, data = api_client.vms.stop(name)
    deadline = datetime.now() + timedelta(seconds=timeout_secs)
    while deadline > datetime.now():
        _, data = api_client.vms.get(name)
        status = data.get("status", {}).get("printableStatus")
        if "Stopped" == status:
            return
        sleep(1)

    raise AssertionError(f"timed out trying to stop {name}")


@pytest.fixture(scope="class")
def source_vm(sourcevm_name, api_client, ssh_keypair, image, wait_timeout):
    yield create_vm(sourcevm_name, api_client, ssh_keypair, image, wait_timeout)
    delete_vm(sourcevm_name, api_client, wait_timeout)


@pytest.fixture(scope="class")
def restored_from_snapshot_vm(api_client, restored_from_snapshot_name,
                              vm_snapshot_name, source_vm, host_shell,
                              vm_shell, ssh_keypair, wait_timeout):
    name, ssh_user = source_vm
    start_vm(name, api_client, wait_timeout)

    def modify(sh):
        _, _ = sh.exec_command("echo 5678 > test.txt && sync")

    vm_shell_do(name, api_client,
                host_shell, vm_shell,
                ssh_user, ssh_keypair,
                modify, wait_timeout)

    # Just to wait for `sync`
    sleep(2)

    stop_vm(name, api_client, wait_timeout)

    spec = api_client.vm_snapshots.RestoreSpec.for_new(restored_from_snapshot_name)
    code, data = api_client.vm_snapshots.restore(vm_snapshot_name, spec)
    assert 201 == code

    deadline = datetime.now() + timedelta(seconds=wait_timeout)
    while deadline > datetime.now():
        code, data = api_client.vms.get(restored_from_snapshot_name)
        if 200 == code and "Running" == data.get("status", {}).get("printableStatus"):
            break
        print("waiting for restored vm to be running")
        sleep(3)
    else:
        raise AssertionError(f"timed out waiting to restore into new VM"
                             f"{restored_from_snapshot_name}")

    yield restored_from_snapshot_name, ssh_user

    delete_vm(restored_from_snapshot_name, api_client, wait_timeout)


@pytest.fixture(scope="class")
def restored_vm_2(api_client, restored_from_snapshot_name_2,
                  vm_snapshot_name, source_vm,
                  host_shell, vm_shell,
                  ssh_keypair, wait_timeout):
    name, ssh_user = source_vm

    start_vm(name, api_client, wait_timeout)

    def modify(sh):
        _, _ = sh.exec_command("echo 99999999 > test.txt && sync")

    vm_shell_do(name, api_client,
                host_shell, vm_shell,
                ssh_user, ssh_keypair,
                modify, wait_timeout)

    # Just to wait for `sync`
    sleep(2)

    stop_vm(name, api_client, wait_timeout)

    spec = api_client.vm_snapshots.RestoreSpec.for_new(restored_from_snapshot_name_2)
    code, data = api_client.vm_snapshots.restore(vm_snapshot_name, spec)
    assert 201 == code

    deadline = datetime.now() + timedelta(seconds=wait_timeout)
    while deadline > datetime.now():
        code, data = api_client.vms.get(restored_from_snapshot_name_2)
        if 200 == code and "Running" == data.get("status", {}).get("printableStatus"):
            break
        print("waiting for restored vm to be running")
        sleep(3)
    else:
        raise AssertionError(f"timed out waiting to restore into new VM"
                             f"{restored_from_snapshot_name_2}")

    yield restored_from_snapshot_name_2, ssh_user

    delete_vm(restored_from_snapshot_name_2, api_client, wait_timeout)


def vm_shell_do(name, api_client, host_shell, vm_shell, user, ssh_keypair, action, wait_timeout):
    _, privatekey = ssh_keypair

    deadline = datetime.now() + timedelta(seconds=wait_timeout)
    while deadline > datetime.now():
        code, data = api_client.vms.get_status(name)
        if 200 == code:
            phase = data.get("status", {}).get("phase")
            conds = data.get("status", {}).get("conditions", [{}])
            if ("Running" == phase
                    and "AgentConnected" == conds[-1].get("type")
                    and data["status"].get("interfaces")):
                break
            sleep(3)

        vm_ip = next(iface["ipAddress"] for iface in data["status"]["interfaces"]
                     if iface["name"] == "default")

        code, data = api_client.hosts.get(data["status"]["nodeName"])
        host_ip = next(addr["address"] for addr in data["status"]["addresses"]
                       if addr["type"] == "InternalIP")

        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(user, pkey=privatekey)

            deadline = datetime.now() + timedelta(seconds=wait_timeout)
            while deadline > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    print(e)
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to {name}")

            with vm_sh as sh:
                action(sh)


@pytest.mark.p0
@pytest.mark.virtualmachines
class TestVMSnapshot:
    @pytest.mark.dependency(name="source_vm_snapshot")
    def test_vm_snapshot_create(self, api_client,
                                source_vm, vm_snapshot_name,
                                host_shell, vm_shell,
                                ssh_keypair, wait_timeout):
        """
        Test that the VM snapshot can be created.

        Prerequisite:
        A virtual machine has been created and is running.
        """
        name, ssh_user = source_vm

        def action(sh):
            _, _ = sh.exec_command("echo 123 > test.txt")
            _, _ = sh.exec_command("sync")

        vm_shell_do(name, api_client,
                    host_shell, vm_shell,
                    ssh_user, ssh_keypair,
                    action, wait_timeout)

        # Since `sync` isn't actually synchronous, wait a couple of
        # seconds to let the I/O flush to disk.
        sleep(2)

        code, _ = api_client.vm_snapshots.create(name, vm_snapshot_name)
        assert 201 == code

        deadline = datetime.now() + timedelta(seconds=wait_timeout)
        while deadline > datetime.now():
            code, data = api_client.vm_snapshots.get(vm_snapshot_name)
            if data.get("status", {}).get("readyToUse"):
                break
            print(f"waiting for {vm_snapshot_name} to be ready")
            sleep(3)
        else:
            raise AssertionError(f"timed out waiting for {vm_snapshot_name} to be ready")

        assert 200 == code
        assert data.get("status", {}).get("readyToUse") is True

    @pytest.mark.dependency(depends=["source_vm_snapshot"])
    def test_restore_into_new_vm_from_vm_snapshot(self, api_client,
                                                  restored_from_snapshot_vm,
                                                  ssh_keypair, host_shell,
                                                  vm_shell, wait_timeout):
        """
        Test that restoring the `vm-snapshot` into a new virtual
        machine results in a virtual machine with the expected
        well-known file (`test.txt`) with the expected contents
        (`123`).

        Prerequisites:
        1. The source VM from the first test case and its
           snapshot (`vm-snapshot`).
        """

        name, ssh_user = restored_from_snapshot_vm

        def actassert(sh):
            out, _ = sh.exec_command("cat test.txt")
            assert "123" in out

        vm_shell_do(name, api_client,
                    host_shell, vm_shell,
                    ssh_user, ssh_keypair,
                    actassert, wait_timeout)

    @pytest.mark.dependency(depends=["source_vm_snapshot"])
    def test_replace_is_rejected_when_deletepolicy_is_retain(self, api_client,
                                                             source_vm, vm_snapshot_name,
                                                             wait_timeout):
        name, _ = source_vm

        stop_vm(name, api_client, wait_timeout)

        """
        Test that the Harvester API rejects a `replace`
        VirtualMachineRestore where the deletePolicy is
        not `retain`.

        Prequisites:
        1. The original VM (`source-vm`) and snapshot (`vm-snapshot`)
        from the first test case.
        """
        spec = api_client.backups.RestoreSpec.for_existing(delete_volumes=True)
        code, data = api_client.vm_snapshots.restore(vm_snapshot_name, spec)

        reason = data.get("message")

        wantmsg = "Delete policy with backup type snapshot"
        " for replacing VM is not supported"

        assert wantmsg in reason
        assert 422 == code

    @pytest.mark.dependency(name="replaced_source_vm", depends=["source_vm_snapshot"])
    def test_replace_vm_with_vm_snapshot(self, api_client,
                                         source_vm, vm_snapshot_name,
                                         ssh_keypair, host_shell,
                                         vm_shell, wait_timeout):
        """
        Test that the original virtual machine can be replaced
        from its original snapshot (`vm-snapshot`) and that
        the snapshot's data contains the well-known file (`test.txt`)
        and its expected contents (`123`).

        Prerequisites:
        `vm-snapshot` VM snapshot exists.
        """
        name, ssh_user = source_vm
        start_vm(name, api_client, wait_timeout)

        def modify(sh):
            _, _ = sh.exec_command("rm -f test.txt && sync")

        vm_shell_do(name, api_client,
                    host_shell, vm_shell,
                    ssh_user, ssh_keypair,
                    modify, wait_timeout)

        # Just to wait for `sync`
        sleep(2)

        stop_vm(name, api_client, wait_timeout)

        spec = api_client.backups.RestoreSpec.for_existing(delete_volumes=False)
        code, data = api_client.vm_snapshots.restore(vm_snapshot_name, spec)

        deadline = datetime.now() + timedelta(seconds=wait_timeout)
        while deadline > datetime.now():
            code, data = api_client.vms.get(name)
            if 200 == code and "Running" == data.get("status", {}).get("printableStatus"):
                break
            print("waiting for restored vm to be running")
            sleep(3)
        assert "Running" == data.get("status", {}).get("printableStatus")

        def actassert(sh):
            out, _ = sh.exec_command("cat test.txt")
            assert "123" in out

        vm_shell_do(name, api_client,
                    host_shell, vm_shell,
                    ssh_user, ssh_keypair,
                    actassert, wait_timeout)

    @pytest.mark.dependency(name="detached_source_vm_pvc", depends=["replaced_source_vm"])
    def test_restore_from_vm_snapshot_while_pvc_detached_from_source(self,
                                                                     api_client,
                                                                     restored_vm_2,
                                                                     host_shell,
                                                                     vm_shell,
                                                                     ssh_keypair,
                                                                     wait_timeout):
        """
        Test that a new virtual machine can be created from a
        VM snapshot created from a source PersistentVolumeClaim
        that is now detached.

        Prerequisites:
        The original VM (`source-vm`) exists and is stopped (so that
        the PVC is detached.)

        The original snapshot (`vm-snapshot`) exists.
        """

        name, ssh_user = restored_vm_2

        def actassert(sh):
            out, _ = sh.exec_command("cat test.txt")
            assert "123" in out

        vm_shell_do(name, api_client,
                    host_shell, vm_shell,
                    ssh_user, ssh_keypair,
                    actassert, wait_timeout)

    @pytest.mark.dependency(name="snapshot_created_from_detached_source_vm_pvc",
                            depends=["detached_source_vm_pvc"])
    def test_create_vm_snapshot_while_pvc_detached(self, api_client,
                                                   vm_snapshot_2_name, source_vm, wait_timeout):
        """
        Test that a VM snapshot can be created when the source
        PVC is detached.

        Prerequisites:
        The original VM (`source-vm`) exists and is stopped (so that
        the PVC is detached.)
        """
        name, _ = source_vm

        stop_vm(name, api_client, wait_timeout)

        code, _ = api_client.vm_snapshots.create(name, vm_snapshot_2_name)
        assert 201 == code

        deadline = datetime.now() + timedelta(seconds=wait_timeout)
        while deadline > datetime.now():
            code, data = api_client.vm_snapshots.get(vm_snapshot_2_name)
            if data.get("status", {}).get("readyToUse"):
                break
            print(f"waiting for {vm_snapshot_2_name} to be ready")
            sleep(3)
        else:
            raise AssertionError(f"timed out waiting for {vm_snapshot_2_name} to be ready")

        code, data = api_client.vm_snapshots.get(vm_snapshot_2_name)

        assert 200 == code
        assert data.get("status", {}).get("readyToUse") is True

    @pytest.mark.dependency(name="cleaned_up_after_vm_delete")
    def test_vm_snapshots_are_cleaned_up_after_source_vm_deleted(self, api_client,
                                                                 source_vm, vm_snapshot_name,
                                                                 wait_timeout):
        """
        Test that VM snapshots are removed when the VM they correspond
        to have been deleted.

        Prerequisites:
        The original VM (`source-vm`) exists and so does its first
        snapshot (`vm-snapshot`).

        Assert that the snapshot exists, then delete the VM
        and assert that the snapshot has been removed.
        """

        code, _ = api_client.vm_snapshots.get(vm_snapshot_name)
        assert 200 == code

        name, _ = source_vm

        code, _ = api_client.vms.delete(name)
        assert 200 == code

        def wait_for_snapshot_to_disappear(snapshot):
            deadline = datetime.now() + timedelta(seconds=wait_timeout)
            while deadline > datetime.now():
                code, _ = api_client.vm_snapshots.get(snapshot)
                if code == 404:
                    return
                sleep(1)
            else:
                AssertionError(f"timeout while waiting for {snapshot}"
                               f" to be deleted after its VM was deleted")

        wait_for_snapshot_to_disappear(vm_snapshot_name)

    @pytest.mark.dependency(depends=["snapshot_created_from_detached_source_vm_pvc",
                                     "cleaned_up_after_vm_delete"])
    def test_volume_snapshots_are_cleaned_up_after_source_volume_deleted(self, api_client,
                                                                         source_vm, wait_timeout):
        """
        Test that any volume snapshots that result from taking
        a VM snapshot while the PVC is detached are cleaned up
        after the volume is deleted.

        Prerequisites:
        The volume from the original VM (`source-vm`) exists
        and is not attached because the original VM was replaced
        and the deletePolicy was `retain`.
        """

        # First, assert that the expected volume exists.
        name, _ = source_vm
        volumename = f"{name}-disk-0"

        code, _ = api_client.volumes.get(volumename)
        assert 200 == code

        # And assert that it has a volume snapshot associated with it.
        volumesnapshotname = f"vm-snapshot-volume-{volumename}"

        code, data = api_client.volsnapshots.get(volumesnapshotname)
        assert 200 == code

        ownerpvc = data.get("spec", {}).get("source", {}).get("persistentVolumeClaimName")
        assert volumename == ownerpvc

        # Then delete the volume and wait for it to disappear.
        code, _ = api_client.volumes.delete(volumename)
        deadline = datetime.now() + timedelta(seconds=wait_timeout)
        while deadline > datetime.now():
            code, _ = api_client.volumes.get(volumename)
            if code == 404:
                break
            sleep(1)
        else:
            raise AssertionError(f"timed out waiting for {volumename} to be deleted")

        # Finally, wait for the volume snapshot to be cleaned up
        # automatically.
        code, _ = api_client.volsnapshots.get(volumesnapshotname)
        while deadline > datetime.now():
            code, _ = api_client.volsnapshots.get(volumesnapshotname)
            if code == 404:
                break
            sleep(1)
        else:
            raise AssertionError(f"timed out waiting for {volumesnapshotname} to be deleted")
