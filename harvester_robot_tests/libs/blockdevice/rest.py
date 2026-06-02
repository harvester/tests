""" Blockdevice Component: REST Implementation

Layer 4: Component and its implementation
"""

from .base import Base


class Rest(Base):
    """REST implementation for Blockdevice operations using Harvester API"""
    def __init__(self):
        super().__init__()

    def list(self, namespace):
        return super().list(namespace)

    def get(self, name, namespace):
        return super().get(name, namespace)

    def provision_longhorn_storage(self, name, engine_version, namespace):
        return super().provision_longhorn_storage(name, engine_version, namespace)
