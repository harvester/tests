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
