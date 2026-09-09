""" Blockdevice Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    def __init__(self):
        self.unsupported_msg = f"Unsupported by {self.__class__.__name__}, falling back."

    @abstractmethod
    def list(self, namespace):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get(self, name, namespace):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def provision_longhorn_storage(self, name, engine_version, namespace):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def identify_lvm_suitable(self, min_size_gib):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def label_lvm_test_disks(self, disk_by_node, run_id):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get_lvm_test_disks(self, run_id):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get_lvm_vg_node(self, run_id, vg_name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def create_lvm_volume_groups(self, disk_by_node, vg_type):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def provision_lvm_disk(self, disk_name, node_name, vg_name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def wait_for_vgs_active(self, vg_node_map, timeout):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def cleanup_lvm_volume_groups(self, disk_by_node):
        raise NotImplementedError(self.unsupported_msg)
