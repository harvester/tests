""" Blockdevice Component: REST Implementation

Layer 4: Component and its implementation
"""

from .base import Base


class Rest(Base):
    """REST implementation for Blockdevice operations using Harvester API"""
    def __init__(self):
        super().__init__()

    def list(self, namespace):
        return super().list(namespace)

    def get(self, name, namespace):
        return super().get(name, namespace)

    def provision_longhorn_storage(self, name, engine_version, namespace):
        return super().provision_longhorn_storage(name, engine_version, namespace)

    def identify_lvm_suitable(self, min_size_gib):
        return super().identify_lvm_suitable(min_size_gib)

    def label_lvm_test_disks(self, disk_by_node, run_id):
        return super().label_lvm_test_disks(disk_by_node, run_id)

    def get_lvm_test_disks(self, run_id):
        return super().get_lvm_test_disks(run_id)

    def get_lvm_vg_node(self, run_id, vg_name):
        return super().get_lvm_vg_node(run_id, vg_name)

    def create_lvm_volume_groups(self, disk_by_node, vg_type):
        return super().create_lvm_volume_groups(disk_by_node, vg_type)

    def provision_lvm_disk(self, disk_name, node_name, vg_name):
        return super().provision_lvm_disk(disk_name, node_name, vg_name)

    def wait_for_vgs_active(self, vg_node_map, timeout):
        return super().wait_for_vgs_active(vg_node_map, timeout)

    def cleanup_lvm_volume_groups(self, disk_by_node):
        return super().cleanup_lvm_volume_groups(disk_by_node)
