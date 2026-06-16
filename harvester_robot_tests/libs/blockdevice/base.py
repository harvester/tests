""" Blockdevice Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    @abstractmethod
    def list(self, namespace):
        """List blockdevices, optionally by namespace

        Return a list of blockdevices
        """
        pass

    @abstractmethod
    def get(self, name, namespace):
        """Get blockdevice, optionally by name and namespace

        Return a blockdevice or None
        """
        pass

    @abstractmethod
    def provision_longhorn_storage(self, name, engine_version, namespace):
        """Provision a blockdevice for Longhorn storage

        Return nothing, but raise exception if operation fails
        """
        pass

    @abstractmethod
    def identify_lvm_suitable(self, min_size_gib):
        """Identify blockdevices >= min_size_gib suitable for LVM.

        Returns dict {node_name: disk_name} with one disk per node.
        """
        pass

    @abstractmethod
    def create_lvm_volume_groups(self, disk_by_node, vg_type):
        """Create LVM volume groups on selected nodes.

        Returns dict {vg_name: node_name}.
        """
        pass

    @abstractmethod
    def provision_lvm_disk(self, disk_name, node_name, vg_name):
        """Provision a blockdevice for LVM with specified volume group"""
        pass

    @abstractmethod
    def wait_for_vgs_active(self, vg_node_map, timeout):
        """Wait for all volume groups in vg_node_map to become active"""
        pass

    @abstractmethod
    def cleanup_lvm_volume_groups(self, disk_by_node):
        """Remove LVM provisioning from disks"""
        pass
