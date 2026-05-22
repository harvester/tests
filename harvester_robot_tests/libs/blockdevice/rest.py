""" Blockdevice Component: REST Implementation

Layer 4: Component and its implementation
"""

from utility.utility import get_harvester_api_client
from .base import Base


class Rest(Base):
    """REST implementation for Blockdevice operations using Harvester API"""

    def __init__(self):
        self.api_client = get_harvester_api_client()
        self.port_forward_process = None

    def list(self, namespace):
        raise NotImplementedError("REST implementation not available for Blockdevice.list")

    def get(self, name, namespace):
        raise NotImplementedError("REST implementation not available for Blockdevice.get")

    def provision_longhorn_storage(self, name, engine_version, namespace):
        raise NotImplementedError("REST implementation not available"
                                  "for Blockdevice.provision_longhorn_storage")

    def identify_lvm_suitable(self, min_size_gib):
        raise NotImplementedError("REST implementation not available"
                                  "for Blockdevice.identify_lvm_suitable")

    def create_lvm_volume_groups(self, disk_by_node, vg_type):
        raise NotImplementedError("REST implementation not available"
                                  "for Blockdevice.create_lvm_volume_groups")

    def provision_lvm_disk(self, disk_name, node_name, vg_name):
        raise NotImplementedError("REST implementation not available"
                                  "for Blockdevice.provision_lvm_disk")

    def wait_for_vgs_active(self, vg_node_map, timeout):
        raise NotImplementedError("REST implementation not available"
                                  "for Blockdevice.wait_for_vgs_active")

    def cleanup_lvm_volume_groups(self, disk_by_node):
        raise NotImplementedError("REST implementation not available"
                                  "for Blockdevice.cleanup_lvm_volume_groups")
