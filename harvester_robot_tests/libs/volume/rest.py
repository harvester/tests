
"""
Volume Rest Implementation - makes actual API calls using get_harvester_api_client()
"""
import time
from datetime import datetime, timedelta
from utility.utility import get_harvester_api_client
from utility.utility import logging
from volume.base import Base


class Rest(Base):
    """Volume Rest implementation - makes actual API calls"""

    def __init__(self):
        pass

    def create(self, volume_name, size, numberOfReplicas, frontend, **kwargs):
        """Create a volume"""
        api = get_harvester_api_client()
        code, data = api.volumes.create(volume_name, size, numberOfReplicas, frontend, **kwargs)
        assert code == 201, f"Failed to create volume: {code}, {data}"
        return data

    def delete(self, volume_name, wait):
        """Delete a volume"""
        api = get_harvester_api_client()
        code, data = api.volumes.delete(volume_name, wait=wait)
        assert code == 200, f"Failed to delete volume: {code}, {data}"

    def attach(self, volume_name, node_name):
        """Attach volume to node"""
        api = get_harvester_api_client()
        code, data = api.volumes.attach(volume_name, node_name)
        assert code == 200, f"Failed to attach volume: {code}, {data}"

    def detach(self, volume_name):
        """Detach volume"""
        api = get_harvester_api_client()
        code, data = api.volumes.detach(volume_name)
        assert code == 200, f"Failed to detach volume: {code}, {data}"

    def wait_for_running(self, volume_name, timeout):
        """Wait for volume to be running"""
        api = get_harvester_api_client()
        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            code, data = api.volumes.get_status(volume_name)
            if code == 200 and data.get('status', {}).get('state') == 'Attached':
                return True
            time.sleep(3)
        raise AssertionError(f"Volume {volume_name} did not reach running state within {timeout}s")

    def wait_for_attached(self, volume_name, timeout):
        """Wait for volume to be attached"""
        return self.wait_for_running(volume_name, timeout)

    def wait_for_deleted(self, volume_name, timeout):
        """Wait for volume to be deleted"""
        api = get_harvester_api_client()
        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            code, data = api.volumes.get(volume_name)
            if code == 404:
                return True
            time.sleep(3)
        raise AssertionError(f"Volume {volume_name} was not deleted within {timeout}s")

    def get_status(self, volume_name):
        """Get volume status"""
        api = get_harvester_api_client()
        code, data = api.volumes.get_status(volume_name)
        assert code == 200, f"Failed to get volume status: {code}, {data}"
        status = data.get('status', {})
        return {
            'state': status.get('state', 'Unknown'),
            'robustness': status.get('robustness', 'Unknown'),
            'replicas': status.get('replicas', {}),
            'last_backup_time': status.get('lastBackupTime', '')
        }

    def list(self):
        """List all volumes"""
        api = get_harvester_api_client()
        code, data = api.volumes.list()
        assert code == 200, f"Failed to list volumes: {code}, {data}"
        volumes = []
        for item in data.get('items', []):
            volumes.append({
                'name': item['metadata']['name'],
                'namespace': item['metadata']['namespace'],
                'creation_time': item['metadata']['creationTimestamp'],
                'status': item.get('status', {})
            })
        return volumes

    def expand(self, volume_name, new_size):
        """Expand volume size"""
        api = get_harvester_api_client()
        code, data = api.volumes.expand(volume_name, new_size)
        assert code == 200, f"Failed to expand volume: {code}, {data}"

    def create_snapshot(self, volume_name, snapshot_name):
        """Create volume snapshot"""
        api = get_harvester_api_client()
        code, data = api.volumes.create_snapshot(volume_name, snapshot_name)
        assert code == 201, f"Failed to create snapshot: {code}, {data}"

    def delete_snapshot(self, volume_name, snapshot_name):
        """Delete volume snapshot"""
        api = get_harvester_api_client()
        code, data = api.volumes.delete_snapshot(volume_name, snapshot_name)
        assert code == 200, f"Failed to delete snapshot: {code}, {data}"

    def restore_from_snapshot(self, volume_name, snapshot_name, new_volume_name):
        """Restore volume from snapshot"""
        api = get_harvester_api_client()
        code, data = api.volumes.restore_from_snapshot(volume_name, snapshot_name, new_volume_name)
        assert code == 201, f"Failed to restore from snapshot: {code}, {data}"

    def cleanup(self):
        """Clean up all test volumes"""
        logging('Cleaning up test volumes')
