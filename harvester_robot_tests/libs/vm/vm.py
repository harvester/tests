
"""
VM Component - delegates to Rest implementation
"""
from constant import HarvesterOperationStrategy
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

    def get_data_checksum(self, vm_name):
        return self.vm.get_data_checksum(vm_name)

    def create_snapshot(self, vm_name, snapshot_name):
        return self.vm.create_snapshot(vm_name, snapshot_name)

    def create_backup(self, vm_name, backup_name):
        return self.vm.create_backup(vm_name, backup_name)

    def wait_for_backup_completed(self, vm_name, backup_name, timeout):
        return self.vm.wait_for_backup_completed(vm_name, backup_name, timeout)

    def cleanup(self):
        return self.vm.cleanup()
