""" Backup Component: REST Implementation

Layer 4: Component and its implementation
"""

from constant import DEFAULT_NAMESPACE, DEFAULT_TIMEOUT_LONG, DEFAULT_TIMEOUT_SHORT
from .base import Base


class Rest(Base):
    """REST implementation for VM backup/restore operations using Harvester API"""

    def __init__(self):
        super().__init__()

    def create(self, vm_name, backup_name, namespace=DEFAULT_NAMESPACE):
        return super().create(vm_name, backup_name, namespace)

    def get(self, backup_name, namespace=DEFAULT_NAMESPACE):
        return super().get(backup_name, namespace)

    def delete(self, backup_name, namespace=DEFAULT_NAMESPACE):
        return super().delete(backup_name, namespace)

    def wait_for_ready(self, backup_name, timeout=DEFAULT_TIMEOUT_LONG,
                       namespace=DEFAULT_NAMESPACE):
        return super().wait_for_ready(backup_name, timeout, namespace)

    def wait_for_deleted(self, backup_name, timeout=DEFAULT_TIMEOUT_SHORT,
                         namespace=DEFAULT_NAMESPACE):
        return super().wait_for_deleted(backup_name, timeout, namespace)

    def restore_to_new_vm(self, backup_name, restore_name, new_vm_name,
                          namespace=DEFAULT_NAMESPACE):
        return super().restore_to_new_vm(backup_name, restore_name, new_vm_name, namespace)

    def restore_replace_vm(self, backup_name, restore_name, delete_volumes=True,
                           namespace=DEFAULT_NAMESPACE):
        return super().restore_replace_vm(backup_name, restore_name, delete_volumes, namespace)

    def wait_for_restore_completed(self, restore_name, timeout=DEFAULT_TIMEOUT_LONG,
                                   namespace=DEFAULT_NAMESPACE):
        return super().wait_for_restore_completed(restore_name, timeout, namespace)

    def delete_restore(self, restore_name, namespace=DEFAULT_NAMESPACE):
        return super().delete_restore(restore_name, namespace)
