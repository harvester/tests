"""
VM Rest Implementation - actual API calls using get_harvester_api_client()
"""
import time
from datetime import datetime, timedelta
from utility.utility import get_harvester_api_client
from utility.utility import get_retry_count_and_interval
from utility.utility import logging
from vm.base import Base


class Rest(Base):
    """VM Rest implementation - makes actual API calls"""

    def __init__(self):
        self.retry_count, self.retry_interval = get_retry_count_and_interval()
        self.checksums = {}

    def create(self, vm_name, cpu, memory, image_id, **kwargs):
        """Create a virtual machine"""
        api = get_harvester_api_client()

        vm_spec = api.vms.Spec(cpu, memory)

        if image_id:
            vm_spec.add_image("disk-0", image_id)

        code, data = api.vms.create(vm_name, vm_spec)
        assert code == 201, f"Failed to create VM: {code}, {data}"
        return data

    def delete(self, vm_name):
        """Delete a virtual machine"""
        api = get_harvester_api_client()
        code, data = api.vms.delete(vm_name)
        assert code == 200, f"Failed to delete VM: {code}, {data}"

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
            code, data = api.vms.get_status(vm_name)
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
        code, data = api.vms.create_snapshot(vm_name, snapshot_name)
        assert code == 201, f"Failed to create snapshot: {code}, {data}"

    def create_backup(self, vm_name, backup_name):
        """Create a backup of the VM"""
        api = get_harvester_api_client()
        code, data = api.vms.create_backup(vm_name, backup_name)
        assert code == 201, f"Failed to create backup: {code}, {data}"

    def wait_for_backup_completed(self, vm_name, backup_name, timeout):
        """Wait for backup to complete"""
        api = get_harvester_api_client()

        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            code, data = api.backups.get(backup_name)
            if code == 200:
                state = data.get('status', {}).get('state')
                if state == 'Ready':
                    return True
                elif state == 'Error':
                    raise AssertionError(f'Backup {backup_name} failed')
            time.sleep(10)

        raise AssertionError(f"Backup did not complete within {timeout}s")

    def cleanup(self):
        """Clean up all VMs"""
        logging('Cleaning up test VMs')
        self.checksums.clear()
