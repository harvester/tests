"""Snapshot Component: REST Implementation (stub)

Layer 4: Component and its implementation
"""

from utility.utility import get_harvester_api_client
from .base import Base


class Rest(Base):
    """REST implementation stub for Snapshot operations"""

    def __init__(self):
        self.api_client = get_harvester_api_client()

    def take_snapshot(self, vm_name, namespace):
        raise NotImplementedError("REST implementation not available for Snapshot.take")

    def wait_for_snapshot_ready(self, snapshot_name, namespace, timeout):
        raise NotImplementedError("REST implementation not available"
                                  "for Snapshot.wait_for_snapshot_ready")

    def delete_snapshot(self, snapshot_name, namespace):
        raise NotImplementedError("REST implementation not available"
                                  "for Snapshot.delete_snapshot")

    def restore_snapshot_to_new_vm(self, snapshot_name, new_vm_name, namespace):
        raise NotImplementedError("REST implementation not available"
                                  "for Snapshot.restore_to_new_vm")

    def restore_snapshot_to_existing_vm(self, snapshot_name, vm_name, namespace):
        raise NotImplementedError("REST implementation not available"
                                  "for Snapshot.restore_to_existing_vm")
