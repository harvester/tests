
"""
VM Keywords - creates VM() instance and delegates - NO direct API calls!
"""
import os
import sys

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))) # noqa E402
from utility.utility import logging # noqa E402
from vm import VM # noqa E402
from snapshot import Snapshot  # noqa E402
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG, DEFAULT_NAMESPACE # noqa E402


class vm_keywords:
    """VM keyword wrapper - creates VM component and delegates"""

    def __init__(self):
        self.vm = VM()
        self._snapshot = None

    @property
    def snapshot(self):
        """Lazy initialize Snapshot to allow API client setup first"""
        if self._snapshot is None:
            self._snapshot = Snapshot()
        return self._snapshot

    def cleanup_vms(self):
        """Clean up all test VMs"""
        self.vm.cleanup()

    def create_vm(self, vm_name, cpu=2, memory="4Gi", image_id="", **kwargs):
        """Create a virtual machine"""
        logging(f'Creating VM {vm_name}')
        self.vm.create(vm_name, cpu, memory, image_id, **kwargs)

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

    def is_vm_running(self, vm_name):
        """Return True if VM is in running state"""
        return self.vm.is_running(vm_name)

    def is_vm_stopped(self, vm_name):
        """Return True if VM is in stopped state"""
        return self.vm.is_stopped(vm_name)

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

    def create_vm_with_volume_using_sc(self, vm_name, sc_name, image_name, network_name=None):
        """Create a VM with Harvester image root disk and LVM StorageClass as additional volume"""
        logging(f'Creating VM {vm_name} with LVM SC {sc_name} and image {image_name}')
        return self.vm.create_vm_with_volume_using_sc(vm_name, sc_name, image_name,
                                                      network_name=network_name)

    def attach_volume_to_vm(self, vm_name, vol_name):
        """Attach an volume to a VM"""
        logging(f'Attaching volume {vol_name} to VM {vm_name}')
        return self.vm.attach_volume(vm_name, vol_name)

    def check_block_device_in_vm(self, vm_name, expected_disk_size=None):
        """Assert the data block device is visible in the VM and return its path"""
        logging(f'Checking block device is available in VM {vm_name}')
        return self.vm.check_block_device(vm_name, expected_disk_size=expected_disk_size)

    def write_data_and_get_checksum_on_disk(self, vm_name, device, format_device=True):
        """Write data to the given device inside the VM and return md5sum checksum"""
        logging(f'Writing data to {device} on VM {vm_name}')
        return self.vm.write_data_and_get_checksum_on_disk(vm_name, device, format_device)

    def delete_data_from_vm(self, vm_name):
        """Delete test data from VM"""
        logging(f'Deleting data from VM {vm_name}')
        return self.vm.delete_data(vm_name)

    def mount_data_disk_in_vm(self, vm_name):
        """Mount the data disk in VM after a restore"""
        logging(f'Mounting data disk in VM {vm_name}')
        return self.vm.mount_data_disk(vm_name)

    def get_data_checksum_from_vm(self, vm_name):
        """Get md5sum checksum of data in VM. Raises if VM not ready or result is invalid."""
        import re
        logging(f'Getting data checksum from VM {vm_name}')
        result = self.vm.get_data_checksum(vm_name)
        if not result or not re.match(r'^[0-9a-f]{32}$', result):
            raise AssertionError(
                f"No valid md5sum from VM {vm_name!r} (got: {result!r:.120})"
            )
        return result

    def expand_volume_via_vm_edit(self, vm_name, vol_name, new_size):
        """Expand a volume by patching the VM spec"""
        logging(f'Expanding volume {vol_name} on VM {vm_name} to {new_size}')
        return self.vm.expand_volume_via_vm_edit(vm_name, vol_name, new_size)

    def get_volume_size_inside_vm(self, vm_name, expected_size):
        """Verify volume size inside VM matches expected; returns True/False"""
        logging(f'Verifying volume size inside VM {vm_name} is {expected_size}')
        return self.vm.verify_volume_size(vm_name, expected_size)
