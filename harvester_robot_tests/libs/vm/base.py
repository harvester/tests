"""
Base class for VM operations (optional - for common patterns)
"""
from abc import ABC, abstractmethod
from constant import DEFAULT_NAMESPACE


class Base(ABC):
    """Base class for VM implementations"""

    @abstractmethod
    def create(self, vm_name, cpu, memory, image_id, **kwargs):
        """Create a virtual machine"""
        pass

    @abstractmethod
    def delete(self, vm_name):
        """Delete a virtual machine"""
        pass

    @abstractmethod
    def start(self, vm_name):
        """Start a VM"""
        pass

    @abstractmethod
    def stop(self, vm_name):
        """Stop a VM"""
        pass

    @abstractmethod
    def restart(self, vm_name):
        """Restart a VM"""
        pass

    @abstractmethod
    def migrate(self, vm_name, target_node):
        """Migrate a VM to a target node"""
        pass

    @abstractmethod
    def wait_for_running(self, vm_name, timeout):
        """Wait for VM to be running"""
        pass

    @abstractmethod
    def wait_for_stopped(self, vm_name, timeout):
        """Wait for VM to be stopped"""
        pass

    @abstractmethod
    def wait_for_deleted(self, vm_name, timeout):
        """Wait for VM to be deleted"""
        pass

    @abstractmethod
    def list(self, namespace=DEFAULT_NAMESPACE):
        """List VMs in a namespace"""
        pass

    @abstractmethod
    def get_status(self, vm_name):
        """Get VM status"""
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up test resources"""
        pass

    @abstractmethod
    def attach_volume(self, vm_name, vol_name, namespace=DEFAULT_NAMESPACE):
        """Attach an existing PVC to a VM (stop, patch, start)"""
        pass

    @abstractmethod
    def is_running(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return True if VM is in Running state"""
        pass

    @abstractmethod
    def is_stopped(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return True if VM is stopped (no VMI)"""
        pass

    @abstractmethod
    def write_data_and_get_checksum_on_disk(
            self, vm_name, device, format_device=True,
            namespace=DEFAULT_NAMESPACE):
        """Write data to the given device inside VM and return md5sum"""
        pass

    @abstractmethod
    def mount_data_disk(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Mount the data disk after a restore"""
        pass

    @abstractmethod
    def delete_data(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Delete test data from VM"""
        pass

    @abstractmethod
    def get_data_checksum(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return md5sum checksum of test data in VM"""
        pass

    @abstractmethod
    def expand_volume_via_vm_edit(self, vm_name, vol_name, new_size, namespace=DEFAULT_NAMESPACE):
        """Expand volume by patching the VM volumeClaimTemplates annotation"""
        pass

    @abstractmethod
    def verify_volume_size(self, vm_name, expected_size, namespace=DEFAULT_NAMESPACE):
        """Verify volume size inside VM matches expected (uses lsblk)"""
        pass
