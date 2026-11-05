""" StorageClass Component

Layer 4: Component and its implementation
"""

from utility.utility import logging
from .base import Base
from .crd import CRD
from .rest import Rest


class StorageClass(Base):
    def __init__(self):
        self.crd = CRD()
        self.rest = Rest()

    def create(self, name, data_engine, number_of_replicas, disk_selector):
        try:
            return self.crd.create(name, data_engine, number_of_replicas, disk_selector)
        except NotImplementedError as e:
            logging(e)
            return self.rest.create(name, data_engine, number_of_replicas, disk_selector)

    def create_lvm(self, name, vg_name, vg_type, node):
        try:
            return self.crd.create_lvm(name, vg_name, vg_type, node)
        except NotImplementedError as e:
            logging(e)
            return self.rest.create_lvm(name, vg_name, vg_type, node)

    def delete(self, name):
        try:
            return self.crd.delete(name)
        except NotImplementedError as e:
            logging(e)
            return self.rest.delete(name)

    def get(self, name):
        try:
            return self.crd.get(name)
        except NotImplementedError as e:
            logging(e)
            return self.rest.get(name)

    def list(self, label_selector=None):
        try:
            return self.crd.list(label_selector)
        except NotImplementedError as e:
            logging(e)
            return self.rest.list(label_selector)

    def get_default(self):
        try:
            return self.crd.get_default()
        except NotImplementedError as e:
            logging(e)
            return self.rest.get_default()

    def set_default(self, name):
        try:
            return self.crd.set_default(name)
        except NotImplementedError as e:
            logging(e)
            return self.rest.set_default(name)

    def unset_default(self, name):
        try:
            return self.crd.unset_default(name)
        except NotImplementedError as e:
            logging(e)
            return self.rest.unset_default(name)

    def cleanup(self):
        try:
            return self.crd.cleanup()
        except NotImplementedError as e:
            logging(e)
            return self.rest.cleanup()
