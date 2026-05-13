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
