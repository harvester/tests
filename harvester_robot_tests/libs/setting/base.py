""" Setting Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    """Base class for Setting implementations"""

    @abstractmethod
    def get(self, setting_id):
        """Get setting details"""
        pass

    @abstractmethod
    def enable(self, setting_id):
        """Enable a setting"""
        pass

    @abstractmethod
    def configure_csi_driver(self, setting_id, provisioner, snapshot_class):
        """Configure csi-driver-config to add a provisioner entry"""
        pass

    @abstractmethod
    def remove_csi_driver(self, setting_id, provisioner):
        """Remove a provisioner entry from csi-driver-config"""
        pass
