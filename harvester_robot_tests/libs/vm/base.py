"""
Base class for VM operations (optional - for common patterns)
"""
from abc import ABC, abstractmethod
from constant import DEFAULT_NAMESPACE, DEFAULT_TIMEOUT_SHORT


class Base(ABC):
    """Base class for VM implementations"""

    @abstractmethod
    def create(self, vm_name, image_id, cpu, memory, **kwargs):
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
    def update_disk_size(self, vm_name, disk_name, new_size, namespace=DEFAULT_NAMESPACE):
        """Update VM disk size via volumeClaimTemplates annotation."""
        pass

    # VM network (NAD) changes, KubeVirt LiveUpdateNADRef
    @abstractmethod
    def try_update_network(self, vm_name, nic_name, network_name,
                           namespace=DEFAULT_NAMESPACE):
        """Change only the NAD (multus.networkName) of a VM network.

        Returns:
            dict: {success, code, message}; never raises on rejection
        """
        pass

    @abstractmethod
    def get_conditions(self, vm_name, from_vmi=False, namespace=DEFAULT_NAMESPACE):
        """Return status.conditions of the VM, or of its VMI"""
        pass

    @abstractmethod
    def get_vmi_networks(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return {network name: NAD} from the running VMI's spec.networks"""
        pass

    @abstractmethod
    def get_vmi_interface_macs(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return {interface name: MAC} from the running VMI's status"""
        pass

    @abstractmethod
    def list_migrations(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return the VM's migrations as dicts with name, phase and failure"""
        pass

    @abstractmethod
    def wait_for_new_migration(self, vm_name, known, name_prefix="",
                               timeout=DEFAULT_TIMEOUT_SHORT,
                               namespace=DEFAULT_NAMESPACE):
        """Wait for a migration not in `known`; return its name"""
        pass

    @abstractmethod
    def wait_for_no_new_migration(self, vm_name, known, duration,
                                  namespace=DEFAULT_NAMESPACE):
        """Fail if a migration not in `known` appears within `duration`"""
        pass

    @abstractmethod
    def wait_for_migration_phase(self, migration_name, phase,
                                 timeout=DEFAULT_TIMEOUT_SHORT,
                                 namespace=DEFAULT_NAMESPACE):
        """Wait until a migration reaches `phase`"""
        pass

    @abstractmethod
    def get_launcher_network_status(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return the Multus network-status of the VMI's current pod"""
        pass
