"""
Snapshot Component - delegates to REST/CRD implementation
"""

import os

from constant import HarvesterOperationStrategy
from snapshot.rest import Rest
from snapshot.crd import CRD
from snapshot.base import Base


class Snapshot(Base):
    _strategy = HarvesterOperationStrategy.CRD

    def __init__(self):
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        try:
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            self._strategy = HarvesterOperationStrategy.CRD

        if self._strategy == HarvesterOperationStrategy.CRD:
            self.snapshot = CRD()
        else:
            self.snapshot = Rest()

    def create(self, vm_name, snapshot_name, **kwargs):
        return self.snapshot.create(vm_name, snapshot_name, **kwargs)

    def delete(self, snapshot_name, **kwargs):
        return self.snapshot.delete(snapshot_name, **kwargs)

    def wait_ready(self, snapshot_name, **kwargs):
        return self.snapshot.wait_ready(snapshot_name, **kwargs)

    def wait_deleted(self, snapshot_name, **kwargs):
        return self.snapshot.wait_deleted(snapshot_name, **kwargs)
