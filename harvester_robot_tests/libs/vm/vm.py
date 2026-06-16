
"""
VM Component - delegates to Rest implementation
"""
from constant import HarvesterOperationStrategy, DEFAULT_NAMESPACE
from vm.rest import Rest
from vm.crd import CRD
from vm.base import Base


class VM(Base):
    # Set desired operation strategy here
    _strategy = HarvesterOperationStrategy.CRD

    def __init__(self):
        if self._strategy == HarvesterOperationStrategy.CRD:
            self.vm = CRD()
        else:
            self.vm = Rest()

    def create(self, vm_name, cpu, memory, image_id, **kwargs):
        return self.vm.create(vm_name, cpu, memory, image_id, **kwargs)

    def delete(self, vm_name):
        return self.vm.delete(vm_name)

    def list(self, namespace=DEFAULT_NAMESPACE):
        return self.vm.list(namespace)

    def start(self, vm_name):
        return self.vm.start(vm_name)

    def stop(self, vm_name):
        return self.vm.stop(vm_name)

    def restart(self, vm_name):
        return self.vm.restart(vm_name)

    def migrate(self, vm_name, target_node):
        return self.vm.migrate(vm_name, target_node)

    def wait_for_running(self, vm_name, timeout):
        return self.vm.wait_for_running(vm_name, timeout)

    def wait_for_stopped(self, vm_name, timeout):
        return self.vm.wait_for_stopped(vm_name, timeout)

    def wait_for_deleted(self, vm_name, timeout):
        return self.vm.wait_for_deleted(vm_name, timeout)

    def get_status(self, vm_name):
        return self.vm.get_status(vm_name)

    def wait_for_ip_addresses(self, vm_name, networks, timeout):
        return self.vm.wait_for_ip_addresses(vm_name, networks, timeout)

    def wait_for_migration_completed(self, vm_name, target_node, timeout):
        return self.vm.wait_for_migration_completed(vm_name, target_node, timeout)

    def verify_on_node(self, vm_name, expected_node):
        return self.vm.verify_on_node(vm_name, expected_node)

    def write_data(self, vm_name, data_size_mb):
        return self.vm.write_data(vm_name, data_size_mb)

    def get_data_checksum(self, vm_name, namespace=None):
        ns = namespace or DEFAULT_NAMESPACE
        return self.vm.get_data_checksum(vm_name, ns)

    def mount_data_disk(self, vm_name, namespace=None):
        ns = namespace or DEFAULT_NAMESPACE
        return self.vm.mount_data_disk(vm_name, ns)

    def create_backup(self, vm_name, backup_name):
        return self.vm.create_backup(vm_name, backup_name)

    def wait_for_backup_completed(self, vm_name, backup_name, timeout):
        return self.vm.wait_for_backup_completed(vm_name, backup_name, timeout)

    def cleanup(self):
        return self.vm.cleanup()

    def attach_volume(self, vm_name, vol_name, namespace=None):
        ns = namespace or DEFAULT_NAMESPACE
        return self.vm.attach_volume(vm_name, vol_name, ns)

    def is_running(self, vm_name, namespace=None):
        ns = namespace or DEFAULT_NAMESPACE
        return self.vm.is_running(vm_name, ns)

    def is_stopped(self, vm_name, namespace=None):
        ns = namespace or DEFAULT_NAMESPACE
        return self.vm.is_stopped(vm_name, ns)

    def check_block_device(self, vm_name, namespace=None, expected_disk_size=None):
        ns = namespace or DEFAULT_NAMESPACE
        return self.vm.check_block_device(vm_name, ns, expected_disk_size)

    def write_data_and_get_checksum_on_disk(
            self, vm_name, device, format_device=True, namespace=None):
        ns = namespace or DEFAULT_NAMESPACE
        return self.vm.write_data_and_get_checksum_on_disk(
            vm_name, device, format_device, ns)

    def create_vm_with_volume_using_sc(self, vm_name, sc_name, image_id,
                                       namespace=None, network_name=None):
        return self.vm.create_vm_with_volume_using_sc(
            vm_name, sc_name, image_id, network_name=network_name)

    def delete_data(self, vm_name, namespace=None):
        ns = namespace or DEFAULT_NAMESPACE
        return self.vm.delete_data(vm_name, ns)

    def expand_volume_via_vm_edit(self, vm_name, vol_name, new_size, namespace=None):
        ns = namespace or DEFAULT_NAMESPACE
        return self.vm.expand_volume_via_vm_edit(vm_name, vol_name, new_size, ns)

    def verify_volume_size(self, vm_name, expected_size, namespace=None):
        ns = namespace or DEFAULT_NAMESPACE
        return self.vm.verify_volume_size(vm_name, expected_size, ns)
