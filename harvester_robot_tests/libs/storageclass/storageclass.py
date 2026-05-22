"""StorageClass Component

Layer 4: Component and its implementation
"""

import os
from constant import HarvesterOperationStrategy
from .base import Base
from .crd import CRD
from .rest import Rest


class StorageClass(Base):
    def __init__(self):
        try:
            strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            self._strategy = HarvesterOperationStrategy.CRD

        match self._strategy:
            case HarvesterOperationStrategy.CRD:
                self.sc = CRD()
            case HarvesterOperationStrategy.REST:
                self.sc = Rest()

    def create_lvm_sc(self, sc_name, vg_name, vg_type, node):
        return self.sc.create_lvm_sc(sc_name, vg_name, vg_type, node)

    def delete(self, sc_name):
        return self.sc.delete(sc_name)

    def get_node(self, sc_name):
        return self.sc.get_node(sc_name)
