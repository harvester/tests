""" Setting Component: REST Implementation

Layer 4: Component and its implementation
"""

from utility.utility import get_harvester_api_client
from .base import Base


class Rest(Base):
    """REST implementation for Setting operations using Harvester API"""

    def __init__(self):
        self.api_client = get_harvester_api_client()
        self.port_forward_process = None

    def get(self, setting_id):
        raise NotImplementedError("REST implementation not available for Setting.get")

    def enable(self, setting_id):
        raise NotImplementedError("REST implementation not available for Setting.enable")

    def configure_csi_driver(self, setting_id, provisioner, snapshot_class):
        raise NotImplementedError("REST implementation not available"
                                  "for Setting.configure_csi_driver")

    def remove_csi_driver(self, setting_id, provisioner):
        raise NotImplementedError("REST implementation not available"
                                  "for Setting.remove_csi_driver")
