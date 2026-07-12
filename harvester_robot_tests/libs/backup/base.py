""" Backup Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod

from constant import DEFAULT_NAMESPACE, DEFAULT_TIMEOUT_LONG, DEFAULT_TIMEOUT_SHORT


class Base(ABC):
    """Base class for VM Backup/Restore implementations"""

    def __init__(self):
        self.unsupported_msg = f"Unsupported by {self.__class__.__name__}, falling back."

    @abstractmethod
    def create(self, vm_name, backup_name, namespace=DEFAULT_NAMESPACE):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get(self, backup_name, namespace=DEFAULT_NAMESPACE):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def delete(self, backup_name, namespace=DEFAULT_NAMESPACE):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def wait_for_ready(self, backup_name, timeout=DEFAULT_TIMEOUT_LONG,
                       namespace=DEFAULT_NAMESPACE):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def wait_for_deleted(self, backup_name, timeout=DEFAULT_TIMEOUT_SHORT,
                         namespace=DEFAULT_NAMESPACE):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def restore_to_new_vm(self, backup_name, restore_name, new_vm_name,
                          namespace=DEFAULT_NAMESPACE):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def restore_replace_vm(self, backup_name, restore_name, delete_volumes=True,
                           namespace=DEFAULT_NAMESPACE):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def wait_for_restore_completed(self, restore_name, timeout=DEFAULT_TIMEOUT_LONG,
                                   namespace=DEFAULT_NAMESPACE):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def delete_restore(self, restore_name, namespace=DEFAULT_NAMESPACE):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get_backup_volume_names(self, backup_name, namespace=DEFAULT_NAMESPACE):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def cleanup_longhorn_backup_artifacts(self, volume_names, image_name,
                                          namespace=DEFAULT_NAMESPACE):
        raise NotImplementedError(self.unsupported_msg)
