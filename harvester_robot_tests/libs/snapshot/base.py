"""Snapshot Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    """Base class for Snapshot implementations"""

    @abstractmethod
    def take_snapshot(self, vm_name, namespace):
        """Take a VM snapshot; returns snapshot_name"""
        pass

    @abstractmethod
    def wait_for_snapshot_ready(self, snapshot_name, namespace, timeout):
        """Wait for a snapshot to be ready"""
        pass

    @abstractmethod
    def delete_snapshot(self, snapshot_name, namespace):
        """Delete a snapshot"""
        pass

    @abstractmethod
    def restore_snapshot_to_new_vm(self, snapshot_name, new_vm_name, namespace):
        """Restore a snapshot to a new VM"""
        pass

    @abstractmethod
    def restore_snapshot_to_existing_vm(self, snapshot_name, vm_name, namespace):
        """Restore a snapshot to an existing VM (must be stopped)"""
        pass
