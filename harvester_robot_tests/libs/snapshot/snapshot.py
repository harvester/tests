"""
Snapshot Component - delegates to REST/CRD implementation
"""

from constant import HarvesterOperationStrategy
from snapshot.rest import Rest
from snapshot.crd import CRD
from snapshot.base import Base


class Snapshot(Base):
    _strategy = HarvesterOperationStrategy.CRD

    def __init__(self):
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
