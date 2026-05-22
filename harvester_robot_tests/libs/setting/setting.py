""" Setting Component

Layer 4: Component and its implementation
"""

import os
from constant import HarvesterOperationStrategy
from .base import Base
from .crd import CRD
from .rest import Rest


class Setting(Base):
    def __init__(self):
        try:
            strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            self._strategy = HarvesterOperationStrategy.CRD

        match self._strategy:
            case HarvesterOperationStrategy.CRD:
                self.setting = CRD()
            case HarvesterOperationStrategy.REST:
                self.setting = Rest()

    def get(self, setting_id):
        """Get setting details - delegates to implementation"""
        setting = self.setting.get(setting_id)
        return setting

    def enable(self, setting_id):
        """Enable a setting - delegates to implementation"""
        setting = self.setting.enable(setting_id)
        return setting

    def configure_csi_driver(self, setting_id, provisioner, snapshot_class):
        """Configure csi-driver-config setting - delegates to implementation"""
        return self.setting.configure_csi_driver(setting_id, provisioner, snapshot_class)

    def remove_csi_driver(self, setting_id, provisioner):
        """Remove a provisioner entry from csi-driver-config - delegates to implementation"""
        return self.setting.remove_csi_driver(setting_id, provisioner)
