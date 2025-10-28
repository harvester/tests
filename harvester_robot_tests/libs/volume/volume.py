
"""
Volume Component - delegates to Rest implementation
"""
from constant import HarvesterOperationStrategy
from volume.rest import Rest
from volume.crd import CRD
from volume.base import Base


class Volume(Base):
    # Set desired operation strategy here
    _strategy = HarvesterOperationStrategy.CRD

    def __init__(self):
        if self._strategy == HarvesterOperationStrategy.CRD:
            self.volume = CRD()
        else:
            self.volume = Rest()

    def create(self, volume_name, size, numberOfReplicas, frontend, **kwargs):
        return self.volume.create(volume_name, size, numberOfReplicas, frontend, **kwargs)

    def delete(self, volume_name, wait):
        return self.volume.delete(volume_name, wait)

    def attach(self, volume_name, node_name):
        return self.volume.attach(volume_name, node_name)

    def detach(self, volume_name):
        return self.volume.detach(volume_name)

    def wait_for_running(self, volume_name, timeout):
        return self.volume.wait_for_running(volume_name, timeout)

    def wait_for_attached(self, volume_name, timeout):
        return self.volume.wait_for_attached(volume_name, timeout)

    def wait_for_deleted(self, volume_name, timeout):
        return self.volume.wait_for_deleted(volume_name, timeout)

    def get_status(self, volume_name):
        return self.volume.get_status(volume_name)

    def list(self):
        return self.volume.list()

    def expand(self, volume_name, new_size):
        return self.volume.expand(volume_name, new_size)

    def create_snapshot(self, volume_name, snapshot_name):
        return self.volume.create_snapshot(volume_name, snapshot_name)

    def delete_snapshot(self, volume_name, snapshot_name):
        return self.volume.delete_snapshot(volume_name, snapshot_name)

    def restore_from_snapshot(self, volume_name, snapshot_name, new_volume_name):
        return self.volume.restore_from_snapshot(volume_name, snapshot_name, new_volume_name)

    def cleanup(self):
        return self.volume.cleanup()
