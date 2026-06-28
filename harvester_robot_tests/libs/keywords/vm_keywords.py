
"""
VM Keywords - creates VM() instance and delegates - NO direct API calls!
"""
import os
import sys

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))) # noqa E402
from utility.utility import logging # noqa E402
from vm import VM # noqa E402
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG, DEFAULT_NAMESPACE # noqa E402


class vm_keywords:
    """VM keyword wrapper - creates VM component and delegates"""

    def __init__(self):
        self.vm = VM()

    def cleanup_vms(self):
        """Clean up all test VMs"""
        self.vm.cleanup()

    def create_vm(self, vm_name, image_id, cpu=2, memory="4Gi", **kwargs):
        """Create a virtual machine"""
        logging(f'Creating VM {vm_name} with image {image_id}, {cpu}C/{memory} and {kwargs}')
        self.vm.create(vm_name, image_id, cpu, memory, **kwargs)

    def delete_vm(self, vm_name):
        """Delete a virtual machine"""
        logging(f'Deleting VM {vm_name}')
        self.vm.delete(vm_name)

    def list_vms(self, namespace=DEFAULT_NAMESPACE, name_prefix=None):
        """List VMs, optionally filtered by name prefix"""
        logging(f'Listing VMs in namespace {namespace}'
                + (f' with prefix {name_prefix}' if name_prefix else ''))
        vms = self.vm.list(namespace)
        if name_prefix:
            vms = [vm for vm in vms
                   if vm.get("metadata", {}).get("name", "").startswith(name_prefix)]
        return [vm.get("metadata", {}).get("name") for vm in vms]

    def start_vm(self, vm_name):
        """Start a stopped VM"""
        logging(f'Starting VM {vm_name}')
        self.vm.start(vm_name)

    def stop_vm(self, vm_name):
        """Stop a running VM"""
        logging(f'Stopping VM {vm_name}')
        self.vm.stop(vm_name)

    def restart_vm(self, vm_name):
        """Restart a VM"""
        logging(f'Restarting VM {vm_name}')
        self.vm.restart(vm_name)

    def migrate_vm(self, vm_name, target_node):
        """Migrate VM to target node"""
        logging(f'Migrating VM {vm_name} to {target_node}')
        self.vm.migrate(vm_name, target_node)

    def pause_vm(self, vm_name):
        """Pause a running VM"""
        logging(f'Pausing VM {vm_name}')
        self.vm.pause(vm_name)

    def unpause_vm(self, vm_name):
        """Unpause a paused VM"""
        logging(f'Unpausing VM {vm_name}')
        self.vm.unpause(vm_name)

    def wait_for_vm_paused(self, vm_name, timeout=DEFAULT_TIMEOUT):
        """Wait for a VM to be paused"""
        logging(f'Waiting for VM {vm_name} to be paused')
        self.vm.wait_for_paused(vm_name, timeout)

    def try_get_vm(self, vm_name):
        """Attempt to get a VM for negative testing; returns result dict"""
        logging(f'Attempting to get VM {vm_name} (negative test)')
        return self.vm.try_get(vm_name)

    def try_delete_vm(self, vm_name):
        """Attempt to delete a VM for negative testing; returns result dict"""
        logging(f'Attempting to delete VM {vm_name} (negative test)')
        return self.vm.try_delete(vm_name)

    def add_volume_to_vm(self, vm_name, disk_name, volume_name):
        """Hot-plug an existing volume into a running VM"""
        logging(f'Hot-plugging volume {volume_name} as {disk_name} into {vm_name}')
        self.vm.add_volume(vm_name, disk_name, volume_name)

    def remove_volume_from_vm(self, vm_name, disk_name):
        """Hot-unplug a disk from a running VM"""
        logging(f'Hot-unplugging disk {disk_name} from {vm_name}')
        self.vm.remove_volume(vm_name, disk_name)

    def wait_for_vm_volume_hotplugged(self, vm_name, disk_name, timeout=DEFAULT_TIMEOUT):
        """Wait for a hot-plugged disk to be Ready"""
        self.vm.wait_for_volume_hotplugged(vm_name, disk_name, timeout)

    def wait_for_vm_volume_unplugged(self, vm_name, disk_name, timeout=DEFAULT_TIMEOUT):
        """Wait for a disk to be detached"""
        self.vm.wait_for_volume_unplugged(vm_name, disk_name, timeout)

    def get_vm_disk_names(self, vm_name):
        """Return the disk names declared in the VM spec"""
        return self.vm.get_disk_names(vm_name)

    def wait_for_vm_running(self, vm_name, timeout=DEFAULT_TIMEOUT):
        """Wait for VM to reach running state"""
        logging(f'Waiting for VM {vm_name} to be running')
        self.vm.wait_for_running(vm_name, timeout)

    def wait_for_vm_stopped(self, vm_name, timeout=DEFAULT_TIMEOUT):
        """Wait for VM to stop"""
        logging(f'Waiting for VM {vm_name} to be stopped')
        self.vm.wait_for_stopped(vm_name, timeout)

    def wait_for_vm_deleted(self, vm_name, timeout=DEFAULT_TIMEOUT):
        """Wait for VM to be deleted"""
        logging(f'Waiting for VM {vm_name} to be deleted')
        self.vm.wait_for_deleted(vm_name, timeout)

    def wait_for_vm_ip_addresses(self, vm_name, networks, timeout=DEFAULT_TIMEOUT):
        """Wait for VM to get IP addresses"""
        logging(f'Waiting for VM {vm_name} to get IP addresses')
        self.vm.wait_for_ip_addresses(vm_name, networks, timeout)

    def wait_for_vm_migration_completed(self, vm_name, target_node, timeout=DEFAULT_TIMEOUT):
        """Wait for VM migration to complete"""
        logging(f'Waiting for VM {vm_name} migration to {target_node}')
        self.vm.wait_for_migration_completed(vm_name, target_node, timeout)

    def verify_vm_on_node(self, vm_name, expected_node):
        """Verify VM is running on expected node"""
        self.vm.verify_on_node(vm_name, expected_node)

    def write_vm_data(self, vm_name, data_size_mb):
        """Write data to VM"""
        logging(f'Writing {data_size_mb}MB data to VM {vm_name}')
        return self.vm.write_data(vm_name, data_size_mb)

    def get_vm_data_checksum(self, vm_name):
        """Get checksum of data in VM"""
        logging(f'Getting data checksum for VM {vm_name}')
        return self.vm.get_data_checksum(vm_name)

    def create_vm_snapshot(self, vm_name, snapshot_name):
        """Create a snapshot of the VM"""
        logging(f'Creating snapshot {snapshot_name} for VM {vm_name}')
        self.vm.create_snapshot(vm_name, snapshot_name)

    def create_vm_backup(self, vm_name, backup_name):
        """Create a backup of the VM"""
        logging(f'Creating backup {backup_name} for VM {vm_name}')
        self.vm.create_backup(vm_name, backup_name)

    def wait_for_backup_completed(self, vm_name, backup_name, timeout=DEFAULT_TIMEOUT_LONG):
        """Wait for backup to complete"""
        logging(f'Waiting for backup {backup_name} to complete')
        self.vm.wait_for_backup_completed(vm_name, backup_name, timeout)

    def update_vm_disk_size(self, vm_name, disk_name, new_size, namespace=DEFAULT_NAMESPACE):
        """Update VM disk size via volumeClaimTemplates annotation."""
        self.vm.update_disk_size(vm_name, disk_name, new_size, namespace)
