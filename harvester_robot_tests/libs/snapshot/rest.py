from utility.utility import get_retry_count_and_interval
from snapshot.base import Base


class Rest(Base):

    def __init__(self):
        self.retry_count, self.retry_interval = get_retry_count_and_interval()
        self.checksums = {}

    def create(self, vm_name, snapshot_name, **kwargs):
        raise NotImplementedError("Snapshot REST strategy is not implemented yet")

    def restore_to_new_vm(self, snapshot_name, new_vm_name, **kwargs):
        raise NotImplementedError(
            "restore_to_new_vm is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd")

    def delete(self, snapshot_name, **kwargs):
        raise NotImplementedError("Snapshot REST strategy is not implemented yet")

    def wait_ready(self, snapshot_name, **kwargs):
        raise NotImplementedError("Snapshot REST strategy is not implemented yet")

    def wait_deleted(self, snapshot_name, **kwargs):
        raise NotImplementedError("Snapshot REST strategy is not implemented yet")
