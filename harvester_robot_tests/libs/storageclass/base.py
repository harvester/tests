"""StorageClass Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    """Base class for StorageClass implementations"""

    @abstractmethod
    def create_lvm_sc(self, sc_name, vg_name, vg_type, node):
        """Create an LVM StorageClass"""
        pass

    @abstractmethod
    def delete(self, sc_name):
        """Delete a StorageClass"""
        pass

    @abstractmethod
    def get_node(self, sc_name):
        """Get the node parameter from a StorageClass"""
        pass
