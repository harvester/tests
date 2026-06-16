""" Blockdevice Component

Layer 4: Component and its implementation
"""

import os
from constant import HarvesterOperationStrategy
from .base import Base
from .crd import CRD
from .rest import Rest


class Blockdevice(Base):
    def __init__(self):
        """Initialize Blockdevice component"""
        try:
            strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            self._strategy = HarvesterOperationStrategy.CRD

        match self._strategy:
            case HarvesterOperationStrategy.CRD:
                self.blockdevice = CRD()
            case HarvesterOperationStrategy.REST:
                self.blockdevice = Rest()

    def list(self, namespace):
        blockdevices = self.blockdevice.list(namespace)
        return blockdevices

    def get(self, name, namespace):
        blockdevice = self.blockdevice.get(name, namespace)
        return blockdevice

    def provision_longhorn_storage(self, name, engine_version, namespace):
        self.blockdevice.provision_longhorn_storage(name, engine_version, namespace)

    def identify_lvm_suitable(self, min_size_gib):
        return self.blockdevice.identify_lvm_suitable(min_size_gib)

    def create_lvm_volume_groups(self, disk_by_node, vg_type):
        return self.blockdevice.create_lvm_volume_groups(disk_by_node, vg_type)

    def provision_lvm_disk(self, disk_name, node_name, vg_name):
        return self.blockdevice.provision_lvm_disk(disk_name, node_name, vg_name)

    def wait_for_vgs_active(self, vg_node_map, timeout=None):
        if timeout is not None:
            return self.blockdevice.wait_for_vgs_active(vg_node_map, timeout)
        return self.blockdevice.wait_for_vgs_active(vg_node_map)

    def cleanup_lvm_volume_groups(self, disk_by_node):
        return self.blockdevice.cleanup_lvm_volume_groups(disk_by_node)
