"""Snapshot Component

Layer 4: Component and its implementation
"""

import os
from constant import HarvesterOperationStrategy
from .base import Base
from .crd import CRD
from .rest import Rest


class Snapshot(Base):
    def __init__(self):
        try:
            strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            self._strategy = HarvesterOperationStrategy.CRD

        match self._strategy:
            case HarvesterOperationStrategy.CRD:
                self.snapshot = CRD()
            case HarvesterOperationStrategy.REST:
                self.snapshot = Rest()

    def take_snapshot(self, vm_name, namespace):
        return self.snapshot.take_snapshot(vm_name, namespace)

    def wait_for_snapshot_ready(self, snapshot_name, namespace, timeout):
        return self.snapshot.wait_for_snapshot_ready(snapshot_name, namespace, timeout)

    def delete_snapshot(self, snapshot_name, namespace):
        return self.snapshot.delete_snapshot(snapshot_name, namespace)

    def restore_snapshot_to_new_vm(self, snapshot_name, new_vm_name, namespace):
        return self.snapshot.restore_snapshot_to_new_vm(snapshot_name, new_vm_name, namespace)

    def restore_snapshot_to_existing_vm(self, snapshot_name, vm_name, namespace):
        return self.snapshot.restore_snapshot_to_existing_vm(snapshot_name, vm_name, namespace)
