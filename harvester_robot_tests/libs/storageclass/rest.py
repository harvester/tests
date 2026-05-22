"""StorageClass Component: REST Implementation (stub)

Layer 4: Component and its implementation
"""

from utility.utility import get_harvester_api_client
from .base import Base


class Rest(Base):
    """REST implementation stub for StorageClass operations"""

    def __init__(self):
        self.api_client = get_harvester_api_client()

    def create_lvm_sc(self, sc_name, vg_name, vg_type, node):
        raise NotImplementedError(
            "REST implementation not available for StorageClass.create_lvm_sc")

    def delete(self, sc_name):
        raise NotImplementedError("REST implementation not available for StorageClass.delete")

    def get_node(self, sc_name):
        raise NotImplementedError("REST implementation not available for StorageClass.get_node")
