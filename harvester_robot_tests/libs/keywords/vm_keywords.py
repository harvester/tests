
"""
VM Keywords - creates VM() instance and delegates - NO direct API calls!
"""

from utility.utility import logging
from vm import VM
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG


class vm_keywords:
    """VM keyword wrapper - creates VM component and delegates"""

    def __init__(self):
        self.vm = VM()

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
