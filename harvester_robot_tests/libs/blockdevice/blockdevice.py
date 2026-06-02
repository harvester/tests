""" Blockdevice Component

Layer 4: Component and its implementation
"""

from utility.utility import logging
from .base import Base
from .crd import CRD
from .rest import Rest


class Blockdevice(Base):
    def __init__(self):
        """Initialize Blockdevice component"""
        self.crd = CRD()
        self.rest = Rest()

    def list(self, namespace):
        try:
            return self.crd.list(namespace)
        except NotImplementedError as e:
            logging(e)
            return self.rest.list(namespace)

    def get(self, name, namespace):
        try:
            return self.crd.get(name, namespace)
        except NotImplementedError as e:
            logging(e)
            return self.rest.get(name, namespace)

    def provision_longhorn_storage(self, name, engine_version, namespace):
        try:
            self.crd.provision_longhorn_storage(name, engine_version, namespace)
        except NotImplementedError as e:
            logging(e)
            self.rest.provision_longhorn_storage(name, engine_version, namespace)
