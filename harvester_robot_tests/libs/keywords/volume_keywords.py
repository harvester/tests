
"""
Layer 3: Volume Keywords - creates Volume() instance and delegates - NO direct API calls!
"""

from utility.utility import logging
from volume import Volume
from constant import DEFAULT_TIMEOUT_SHORT


class volume_keywords:
    """Layer 3: Volume keyword wrapper - creates Volume component and delegates"""

    def __init__(self):
        self.volume = Volume()

    def cleanup_volumes(self):
        """Clean up all test volumes"""
        self.volume.cleanup()

    def create_volume(self, volume_name, size="2Gi", numberOfReplicas=3, frontend="blockdev", **kwargs):    # NOQA
        """Create a volume"""
        logging(f'Creating volume {volume_name}')
        self.volume.create(volume_name, size, numberOfReplicas, frontend, **kwargs)

    def delete_volume(self, volume_name, wait=True):
        """Delete a volume"""
        logging(f'Deleting volume {volume_name}')
        self.volume.delete(volume_name, wait)

    def attach_volume(self, volume_name, node_name):
        """Attach volume to node"""
        logging(f'Attaching volume {volume_name} to node {node_name}')
        self.volume.attach(volume_name, node_name)

    def detach_volume(self, volume_name):
        """Detach volume"""
        logging(f'Detaching volume {volume_name}')
        self.volume.detach(volume_name)

    def wait_for_volume_running(self, volume_name, timeout=DEFAULT_TIMEOUT_SHORT):
        """Wait for volume to be running"""
        logging(f'Waiting for volume {volume_name} to be running')
        self.volume.wait_for_running(volume_name, timeout)

    def wait_for_volume_attached(self, volume_name, timeout=DEFAULT_TIMEOUT_SHORT):
        """Wait for volume to be attached"""
        logging(f'Waiting for volume {volume_name} to be attached')
        self.volume.wait_for_attached(volume_name, timeout)

    def wait_for_volume_deleted(self, volume_name, timeout=DEFAULT_TIMEOUT_SHORT):
        """Wait for volume to be deleted"""
        logging(f'Waiting for volume {volume_name} to be deleted')
        self.volume.wait_for_deleted(volume_name, timeout)

    def get_volume_status(self, volume_name):
        """Get volume status"""
        logging(f'Getting status for volume {volume_name}')
        return self.volume.get_status(volume_name)

    def list_volumes(self):
        """List all volumes"""
        logging('Listing all volumes')
        return self.volume.list()

    def expand_volume(self, volume_name, new_size):
        """Expand volume size"""
        logging(f'Expanding volume {volume_name} to {new_size}')
        self.volume.expand(volume_name, new_size)

    def create_volume_snapshot(self, volume_name, snapshot_name):
        """Create volume snapshot"""
        logging(f'Creating snapshot {snapshot_name} for volume {volume_name}')
        self.volume.create_snapshot(volume_name, snapshot_name)

    def delete_volume_snapshot(self, volume_name, snapshot_name):
        """Delete volume snapshot"""
        logging(f'Deleting snapshot {snapshot_name} from volume {volume_name}')
        self.volume.delete_snapshot(volume_name, snapshot_name)

    def restore_volume_from_snapshot(self, volume_name, snapshot_name, new_volume_name):
        """Restore volume from snapshot"""
        logging(f'Restoring volume from snapshot {snapshot_name}')
        self.volume.restore_from_snapshot(volume_name, snapshot_name, new_volume_name)
