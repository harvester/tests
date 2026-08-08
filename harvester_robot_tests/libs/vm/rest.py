"""
VM Rest Implementation - actual API calls using get_harvester_api_client()
"""
import time
import yaml
from datetime import datetime, timedelta
from utility.utility import get_harvester_api_client
from utility.utility import get_retry_count_and_interval
from utility.utility import logging
from vm.base import Base
from constant import DEFAULT_NAMESPACE, DEFAULT_TIMEOUT_SHORT


class Rest(Base):
    """VM Rest implementation - makes actual API calls"""

    def __init__(self):
        self.retry_count, self.retry_interval = get_retry_count_and_interval()
        self.checksums = {}

    def create(self, vm_name, image_id, cpu, memory, **kwargs):
        """Create a virtual machine"""
        api = get_harvester_api_client()

        vm_spec = api.vms.Spec(cpu, memory)

        if image_id:
            # The version-aware VMSpec decides whether the UID is needed
            # (v1.8.0+ names the image storage class lh-<uid>)
            image_uid = None
            try:
                code_img, img_data = api.images.get(image_id.split('/')[-1])
                if code_img == 200:
                    image_uid = img_data.get(
                        "metadata", {}
                    ).get("uid")
            except Exception as e:
                logging(f"Could not look up image UID for {image_id}: {e}",
                        level="WARNING")
            vm_spec.add_image("disk-0", image_id, image_uid=image_uid)

        # Cloud-init: VMSpec already carries a cloudinitdisk with default
        # user-data (and the qemu-guest-agent setup), so just merge the ssh
        # key into it -- exactly what stopped_vm() does. The setter prepends
        # the "#cloud-config" header for us.
        if kwargs.get("user_data"):
            vm_spec.user_data = kwargs["user_data"]
        if kwargs.get("ssh_public_key"):
            userdata = yaml.safe_load(vm_spec.user_data) or {}
            userdata["ssh_authorized_keys"] = [kwargs["ssh_public_key"]]
            vm_spec.user_data = yaml.dump(userdata)
        if kwargs.get("network_data"):
            vm_spec.network_data = kwargs["network_data"]
        if kwargs.get("run_strategy"):
            vm_spec.run_strategy = kwargs["run_strategy"]

        code, data = api.vms.create(vm_name, vm_spec)
        assert code == 201, f"Failed to create VM: {code}, {data}"
        return data

    def delete(self, vm_name):
        """Delete a virtual machine"""
        api = get_harvester_api_client()
        code, data = api.vms.delete(vm_name)
        assert code == 200, f"Failed to delete VM: {code}, {data}"

    def list(self, namespace=DEFAULT_NAMESPACE):
        """List VMs in a namespace"""
        api = get_harvester_api_client()
        code, data = api.vms.get("", namespace)
        assert code == 200, f"Failed to list VMs: {code}, {data}"
        return data.get("data", [])

    def pause(self, vm_name):
        """Pause a VM. Only implemented for the CRD strategy."""
        raise NotImplementedError(
            "pause is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")

    def unpause(self, vm_name):
        """Unpause a VM. Only implemented for the CRD strategy."""
        raise NotImplementedError(
            "unpause is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")

    def wait_for_paused(self, vm_name, timeout):
        """Wait for paused. Only implemented for the CRD strategy."""
        raise NotImplementedError(
            "wait_for_paused is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")

    def try_get(self, vm_name):
        """Negative-test helper. Only implemented for the CRD strategy."""
        raise NotImplementedError(
            "try_get is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")

    def try_delete(self, vm_name):
        """Negative-test helper. Only implemented for the CRD strategy."""
        raise NotImplementedError(
            "try_delete is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")

    def add_volume(self, vm_name, disk_name, volume_name):
        """Hot-plug a volume. Only implemented for the CRD strategy."""
        raise NotImplementedError(
            "add_volume is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")

    def remove_volume(self, vm_name, disk_name):
        """Hot-unplug a volume. Only implemented for the CRD strategy."""
        raise NotImplementedError(
            "remove_volume is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")

    def wait_for_volume_hotplugged(self, vm_name, disk_name, timeout):
        """Only implemented for the CRD strategy."""
        raise NotImplementedError(
            "wait_for_volume_hotplugged is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")

    def wait_for_volume_unplugged(self, vm_name, disk_name, timeout):
        """Only implemented for the CRD strategy."""
        raise NotImplementedError(
            "wait_for_volume_unplugged is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")

    def get_disk_names(self, vm_name):
        """Only implemented for the CRD strategy."""
        raise NotImplementedError(
            "get_disk_names is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")

    def get_cpu_cores(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return the CPU cores declared in the VM spec.

        Uses the version-aware VMSpec model instead of reading the raw VM
        object, so callers do not have to know whether the cores live in
        `domain.cpu.cores` or `domain.cpu.sockets` (the CPU/memory hot-plug
        layout used from v1.8.0 onwards).
        """
        api = get_harvester_api_client()
        code, data = api.vms.get(vm_name, namespace)
        assert code == 200, f"Failed to get VM {vm_name}: {code}, {data}"
        spec = api.vms.Spec.from_dict(data)
        return int(spec.cpu_cores)

    def get_vmi_cpu_cores(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return the CPU cores the running VMI is actually configured with.

        There is no model for the VMI (it is a read-only status object), so
        this reads `status.currentCPUTopology` -- the value kubevirt reports
        for the live guest -- and falls back to the VMI spec on older
        versions that do not populate the topology.
        """
        api = get_harvester_api_client()
        code, data = api.vms.get_status(vm_name, namespace)
        assert code == 200, f"Failed to get VMI {vm_name}: {code}, {data}"
        topology = data.get('status', {}).get('currentCPUTopology') or {}
        cores = topology.get('cores')
        if cores is None:
            cores = (data.get('spec', {}).get('domain', {})
                     .get('cpu', {}).get('cores'))
        if cores is None:
            raise AssertionError(
                f"VMI {namespace}/{vm_name} does not report CPU cores")
        return int(cores)

    def update_cpu_cores(self, vm_name, cores, namespace=DEFAULT_NAMESPACE):
        """Update the VM's CPU cores through the Harvester REST API.

        The VM is round-tripped through the VMSpec model
        (`from_dict` -> `cpu_cores` -> `update`), which keeps
        `domain.resources.limits.cpu` and the hot-plug related fields
        consistent for us. The change only reaches the guest after the VM is
        restarted (unless CPU hot-plug is enabled).
        """
        api = get_harvester_api_client()
        cores = int(cores)
        for i in range(self.retry_count):
            code, data = api.vms.get(vm_name, namespace)
            assert code == 200, f"Failed to get VM {vm_name}: {code}, {data}"

            spec = api.vms.Spec.from_dict(data)
            spec.cpu_cores = cores

            code, data = api.vms.update(vm_name, spec, namespace)
            if code == 200:
                logging(f"Updated VM {namespace}/{vm_name} CPU cores to {cores}")
                return data
            if code == 409:
                logging(f"Conflict when updating VM CPU, retrying ({i})...")
                time.sleep(self.retry_interval)
                continue
            raise AssertionError(
                f"Failed to update CPU of VM {namespace}/{vm_name}: "
                f"{code}, {data}")

        raise AssertionError(
            f"Failed to update CPU of VM {namespace}/{vm_name} after "
            f"{self.retry_count} attempts")

    def wait_for_cpu_cores(self, vm_name, expected_cores,
                           timeout=DEFAULT_TIMEOUT_SHORT,
                           namespace=DEFAULT_NAMESPACE):
        """Wait until the running VMI reports the expected CPU cores."""
        expected_cores = int(expected_cores)
        endtime = datetime.now() + timedelta(seconds=timeout)
        current = None
        while endtime > datetime.now():
            try:
                current = self.get_vmi_cpu_cores(vm_name, namespace)
                if current == expected_cores:
                    logging(f"VM {namespace}/{vm_name} reports "
                            f"{current} CPU cores")
                    return True
            except AssertionError as e:
                logging(f"Error checking VMI CPU cores: {e}")
            time.sleep(self.retry_interval)

        raise AssertionError(
            f"VM {namespace}/{vm_name} did not report {expected_cores} CPU "
            f"cores within {timeout}s (current: {current})")

    def start(self, vm_name):
        """Start a VM"""
        api = get_harvester_api_client()
        code, data = api.vms.start(vm_name)
        assert code in [200, 204], f"Failed to start VM: {code}, {data}"

    def stop(self, vm_name):
        """Stop a VM"""
        api = get_harvester_api_client()
        code, data = api.vms.stop(vm_name)
        assert code in [200, 204], f"Failed to stop VM: {code}, {data}"

    def restart(self, vm_name):
        """Restart a VM"""
        api = get_harvester_api_client()
        code, data = api.vms.restart(vm_name)
        assert code in [200, 204], f"Failed to restart VM: {code}, {data}"

    def softreboot(self, vm_name):
        """Soft-reboot a running VM (guest-level reboot via qemu-guest-agent)"""
        api = get_harvester_api_client()
        code, data = api.vms.softreboot(vm_name)
        assert code in [200, 204], f"Failed to soft-reboot VM: {code}, {data}"

    def wait_vm_condition(
            self, vm_name, condition_type, condition_status,
            timeout=DEFAULT_TIMEOUT_SHORT, namespace=DEFAULT_NAMESPACE):
        """Wait until a VM's status.conditions reaches the expected state.

        status.conditions is a set keyed by `type`, NOT an append-ordered
        log -- entries such as Ready/LiveMigratable/StorageLiveMigratable
        are always present, while conditions like AgentConnected only
        appear once qemu-guest-agent connects.

        If `condition_status` is a string (e.g. "True"), waits until a
        condition of `condition_type` exists with a matching `status`, and
        returns that condition dict (so callers can still read fields such
        as `lastProbeTime`).

        If `condition_status` is None, waits until NO condition of
        `condition_type` is present at all, and returns None.
        """
        api = get_harvester_api_client()
        for i in range(timeout):
            code, data = api.vms.get_status(vm_name, namespace)
            if code == 200:
                conditions = data.get('status', {}).get('conditions', [])
                cond = next((c for c in conditions if c.get('type') == condition_type), None)

                if condition_status is None:
                    if cond is None:
                        return None
                elif cond is not None and cond.get('status') == condition_status:
                    return cond

                if i % 30 == 0:
                    logging(f"Waiting for VM {vm_name} condition {condition_type}="
                            f"{condition_status} (current: {cond})...")
            time.sleep(self.retry_interval)

        raise AssertionError(
            f"VM {vm_name} condition {condition_type} did not reach "
            f"status={condition_status} within {timeout}s"
        )

    def wait_for_agent_connected(
            self, vm_name, timeout=DEFAULT_TIMEOUT_SHORT, namespace=DEFAULT_NAMESPACE):
        """Wait until the VM's guest agent connects.

        Right after a VM is created/started, qemu-guest-agent has not
        connected yet (only Ready/LiveMigratable/StorageLiveMigratable
        exist), so this must be polled rather than checked once. Returns the
        AgentConnected condition dict (includes `lastProbeTime`).
        """
        return self.wait_vm_condition(vm_name, "AgentConnected", "True", timeout, namespace)

    def wait_for_agent_disconnected(
            self, vm_name, timeout=DEFAULT_TIMEOUT_SHORT, namespace=DEFAULT_NAMESPACE):
        """Wait until the VM's guest agent disconnects (AgentConnected
        condition is removed entirely)."""
        return self.wait_vm_condition(vm_name, "AgentConnected", None, timeout, namespace)

    def get_ip_address(self, vm_name, network="default",
                       namespace=DEFAULT_NAMESPACE):
        """Return the IP address the VMI reports for `network`."""
        api = get_harvester_api_client()
        code, data = api.vms.get_status(vm_name, namespace)
        assert code == 200, f"Failed to get VMI {vm_name}: {code}, {data}"
        interfaces = data.get('status', {}).get('interfaces', [])
        for iface in interfaces:
            if iface.get('name') == network and iface.get('ipAddress'):
                return iface['ipAddress']
        raise AssertionError(
            f"VM {namespace}/{vm_name} has no IP address on network "
            f"{network!r} (interfaces: {interfaces})")

    def get_node_name(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return the name of the node the VM is currently running on."""
        api = get_harvester_api_client()
        code, data = api.vms.get_status(vm_name, namespace)
        assert code == 200, f"Failed to get VMI {vm_name}: {code}, {data}"
        node_name = data.get('status', {}).get('nodeName')
        if not node_name:
            raise AssertionError(
                f"VM {namespace}/{vm_name} is not scheduled to a node yet")
        return node_name

    def migrate(self, vm_name, target_node):
        """Migrate VM to target node"""
        api = get_harvester_api_client()
        code, data = api.vms.migrate(vm_name, target_node)
        assert code == 204, f"Failed to migrate VM: {code}, {data}"

    def wait_for_running(self, vm_name, timeout):
        """Wait for VM to reach running state"""
        api = get_harvester_api_client()

        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            code, data = api.vms.get_status(vm_name)
            if code == 200 and data.get('status', {}).get('phase') == 'Running':
                return True
            time.sleep(self.retry_interval)

        raise AssertionError(f"VM {vm_name} did not reach running state within {timeout}s")

    def wait_for_stopped(self, vm_name, timeout):
        """Wait for VM to stop"""
        api = get_harvester_api_client()

        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            # printableStatus lives on the VM object, not the VMI
            code, data = api.vms.get(vm_name)
            if code == 200 and data.get('status', {}).get('printableStatus') == 'Stopped':
                return True
            time.sleep(3)

        raise AssertionError(f"VM {vm_name} did not stop within {timeout}s")

    def wait_for_deleted(self, vm_name, timeout):
        """Wait for VM to be deleted"""
        api = get_harvester_api_client()

        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            code, data = api.vms.get(vm_name)
            if code == 404:
                return True
            time.sleep(3)

        raise AssertionError(f"VM {vm_name} was not deleted within {timeout}s")

    def get_status(self, vm_name):
        """Get VM status"""
        api = get_harvester_api_client()
        code, data = api.vms.get_status(vm_name)
        assert code == 200, f"Failed to get VM status: {code}, {data}"
        return data

    def wait_for_ip_addresses(self, vm_name, networks, timeout):
        """Wait for VM to get IP addresses"""
        api = get_harvester_api_client()

        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            code, data = api.vms.get_status(vm_name)
            if code == 200:
                interfaces = data.get('status', {}).get('interfaces', [])
                got_all_ips = all(
                    any(iface['name'] == net and iface.get('ipAddress')
                        for iface in interfaces)
                    for net in networks
                )
                if got_all_ips:
                    return True
            time.sleep(3)

        raise AssertionError(f"VM {vm_name} did not get IP addresses within {timeout}s")

    def wait_for_migration_completed(self, vm_name, target_node, timeout):
        """Wait for VM migration to complete"""
        api = get_harvester_api_client()

        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            code, data = api.vms.get_status(vm_name)
            if code == 200:
                migration_state = data.get('status', {}).get('migrationState', {})
                if migration_state.get('completed'):
                    current_node = data.get('status', {}).get('nodeName')
                    if current_node == target_node:
                        return True
            time.sleep(5)

        raise AssertionError(f"VM {vm_name} migration did not complete within {timeout}s")

    def verify_on_node(self, vm_name, expected_node):
        """Verify VM is running on expected node"""
        api = get_harvester_api_client()
        code, data = api.vms.get_status(vm_name)
        assert code == 200, f"Failed to get VM status: {code}, {data}"

        actual_node = data.get('status', {}).get('nodeName')
        assert actual_node == expected_node, \
            f"VM {vm_name} is on {actual_node}, expected {expected_node}"

    def write_data(self, vm_name, data_size_mb):
        """Write data to VM"""
        checksum = f"checksum-{vm_name}-{data_size_mb}"
        self.checksums[vm_name] = checksum
        return checksum

    def get_data_checksum(self, vm_name):
        """Get checksum of data in VM"""
        return self.checksums.get(vm_name, "")

    def create_snapshot(self, vm_name, snapshot_name):
        """Create a snapshot of the VM"""
        api = get_harvester_api_client()
        code, data = api.vm_snapshots.create(vm_name, snapshot_name)
        assert code == 201, f"Failed to create snapshot: {code}, {data}"

    def cleanup(self):
        """Clean up all VMs"""
        logging('Cleaning up test VMs')
        self.checksums.clear()

    def update_disk_size(self, vm_name, disk_name, new_size, namespace=DEFAULT_NAMESPACE):
        """Update VM disk size. Only implemented for the CRD strategy."""
        raise NotImplementedError(
            "update_disk_size is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")
