from utility.utility import get_retry_count_and_interval
from snapshot.base import Base


class Rest(Base):

    def __init__(self):
        self.retry_count, self.retry_interval = get_retry_count_and_interval()
        self.checksums = {}

    def create(self, vm_name, snapshot_name, **kwargs):
        pass

    def delete(self, snapshot_name, **kwargs):
        pass

    def wait_ready(self, snapshot_name, **kwargs):
        pass

    def wait_deleted(self, snapshot_name, **kwargs):
        pass
