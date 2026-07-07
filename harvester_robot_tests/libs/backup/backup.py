""" Backup Component - delegates to CRD or REST implementation

Layer 4: Component and its implementation
"""
import os

from constant import (
    HarvesterOperationStrategy,
    DEFAULT_NAMESPACE, DEFAULT_TIMEOUT_LONG, DEFAULT_TIMEOUT_SHORT,
)
from backup.base import Base
from backup.crd import CRD
from backup.rest import Rest


class Backup(Base):
    """Backup component - selects implementation by HARVESTER_OPERATION_STRATEGY"""

    def __init__(self):
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        if strategy_str == HarvesterOperationStrategy.REST.value:
            self.backup = Rest()
        else:
            self.backup = CRD()

    def create(self, vm_name, backup_name, namespace=DEFAULT_NAMESPACE):
        return self.backup.create(vm_name, backup_name, namespace)

    def get(self, backup_name, namespace=DEFAULT_NAMESPACE):
        return self.backup.get(backup_name, namespace)

    def delete(self, backup_name, namespace=DEFAULT_NAMESPACE):
        return self.backup.delete(backup_name, namespace)

    def wait_for_ready(self, backup_name, timeout=DEFAULT_TIMEOUT_LONG,
                       namespace=DEFAULT_NAMESPACE):
        return self.backup.wait_for_ready(backup_name, timeout, namespace)

    def wait_for_deleted(self, backup_name, timeout=DEFAULT_TIMEOUT_SHORT,
                         namespace=DEFAULT_NAMESPACE):
        return self.backup.wait_for_deleted(backup_name, timeout, namespace)

    def restore_to_new_vm(self, backup_name, restore_name, new_vm_name,
                          namespace=DEFAULT_NAMESPACE):
        return self.backup.restore_to_new_vm(
            backup_name, restore_name, new_vm_name, namespace)

    def restore_replace_vm(self, backup_name, restore_name, delete_volumes=True,
                           namespace=DEFAULT_NAMESPACE):
        return self.backup.restore_replace_vm(
            backup_name, restore_name, delete_volumes, namespace)

    def wait_for_restore_completed(self, restore_name, timeout=DEFAULT_TIMEOUT_LONG,
                                   namespace=DEFAULT_NAMESPACE):
        return self.backup.wait_for_restore_completed(restore_name, timeout, namespace)

    def delete_restore(self, restore_name, namespace=DEFAULT_NAMESPACE):
        return self.backup.delete_restore(restore_name, namespace)
