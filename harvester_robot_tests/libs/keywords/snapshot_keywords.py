"""
Snapshot Keywords - Layer 3 wrapper around the Snapshot component.
Exposes snapshot lifecycle operations (take, wait, delete) as Robot Framework keywords.
Restore operations remain in vm_keywords because they create/modify VMs.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from utility.utility import logging  # noqa E402
from snapshot import Snapshot  # noqa E402
from constant import DEFAULT_TIMEOUT, DEFAULT_NAMESPACE  # noqa E402


class snapshot_keywords:
    """Snapshot keyword wrapper - creates Snapshot component and delegates"""

    def __init__(self):
        self._snapshot = None

    @property
    def snapshot(self):
        """Lazy initialize Snapshot to allow API client setup first"""
        if self._snapshot is None:
            self._snapshot = Snapshot()
        return self._snapshot

    def take_vm_snapshot(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Take a snapshot of the given VM; returns the snapshot name"""
        logging(f'Taking snapshot of VM {vm_name}')
        return self.snapshot.take_snapshot(vm_name, namespace)

    def wait_for_vm_snapshot_ready(self, snapshot_name, namespace=DEFAULT_NAMESPACE,
                                   timeout=DEFAULT_TIMEOUT):
        """Wait until the snapshot is marked readyToUse"""
        logging(f'Waiting for snapshot {snapshot_name} to be ready')
        self.snapshot.wait_for_snapshot_ready(snapshot_name, namespace, timeout)

    def delete_vm_snapshot(self, snapshot_name, namespace=DEFAULT_NAMESPACE):
        """Delete a VM snapshot"""
        logging(f'Deleting snapshot {snapshot_name}')
        self.snapshot.delete_snapshot(snapshot_name, namespace)

    def restore_snapshot_to_new_vm(self, snapshot_name, new_vm_name,
                                   namespace=DEFAULT_NAMESPACE):
        """Restore a snapshot to a newly created VM"""
        logging(f'Restoring snapshot {snapshot_name} to new VM {new_vm_name}')
        self.snapshot.restore_snapshot_to_new_vm(snapshot_name, new_vm_name, namespace)

    def restore_snapshot_to_existing_vm(self, snapshot_name, vm_name,
                                        namespace=DEFAULT_NAMESPACE):
        """Restore a snapshot to an existing (stopped) VM"""
        logging(f'Restoring snapshot {snapshot_name} to existing VM {vm_name}')
        self.snapshot.restore_snapshot_to_existing_vm(snapshot_name, vm_name, namespace)
