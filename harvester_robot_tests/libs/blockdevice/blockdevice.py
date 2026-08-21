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

    def identify_lvm_suitable(self, min_size_gib):
        try:
            return self.crd.identify_lvm_suitable(min_size_gib)
        except NotImplementedError as e:
            logging(e)
            return self.rest.identify_lvm_suitable(min_size_gib)

    def label_lvm_test_disks(self, disk_by_node, run_id):
        try:
            return self.crd.label_lvm_test_disks(disk_by_node, run_id)
        except NotImplementedError as e:
            logging(e)
            return self.rest.label_lvm_test_disks(disk_by_node, run_id)

    def get_lvm_test_disks(self, run_id):
        try:
            return self.crd.get_lvm_test_disks(run_id)
        except NotImplementedError as e:
            logging(e)
            return self.rest.get_lvm_test_disks(run_id)

    def get_lvm_vg_node(self, run_id, vg_name):
        try:
            return self.crd.get_lvm_vg_node(run_id, vg_name)
        except NotImplementedError as e:
            logging(e)
            return self.rest.get_lvm_vg_node(run_id, vg_name)

    def create_lvm_volume_groups(self, disk_by_node, vg_type):
        try:
            return self.crd.create_lvm_volume_groups(disk_by_node, vg_type)
        except NotImplementedError as e:
            logging(e)
            return self.rest.create_lvm_volume_groups(disk_by_node, vg_type)

    def provision_lvm_disk(self, disk_name, node_name, vg_name):
        try:
            return self.crd.provision_lvm_disk(disk_name, node_name, vg_name)
        except NotImplementedError as e:
            logging(e)
            return self.rest.provision_lvm_disk(disk_name, node_name, vg_name)

    def wait_for_vgs_active(self, vg_node_map, timeout):
        try:
            return self.crd.wait_for_vgs_active(vg_node_map, timeout)
        except NotImplementedError as e:
            logging(e)
            return self.rest.wait_for_vgs_active(vg_node_map, timeout)

    def cleanup_lvm_volume_groups(self, disk_by_node):
        try:
            return self.crd.cleanup_lvm_volume_groups(disk_by_node)
        except NotImplementedError as e:
            logging(e)
            return self.rest.cleanup_lvm_volume_groups(disk_by_node)
