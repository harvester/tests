""" Storage Keyword Wrapper

Layer 3: Keyword wrapper (NO direct API calls)
"""

import os
import sys

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))) # noqa E402
from constant import LARGE_DISK_BYTE  # noqa E402
from utility.utility import logging  # noqa E402
from blockdevice import Blockdevice  # noqa E402
from storageclass import StorageClass  # noqa E402
from host_keywords import host_keywords  # noqa E402


class storage_keywords:
    """Storage keyword wrapper"""

    def __init__(self):
        """Initialize storage keywords with lazy loading"""
        self._blockdevice = None
        self._sc = None
        self._host = None

    @property
    def blockdevice(self):
        """Lazy initialize blockdevice to allow API client setup first"""
        if self._blockdevice is None:
            self._blockdevice = Blockdevice()
        return self._blockdevice

    @property
    def host(self):
        """Lazy initialize host_keywords to allow API client setup first"""
        if self._host is None:
            self._host = host_keywords()
        return self._host

    @property
    def sc(self):
        """Lazy initialize StorageClass to allow API client setup first"""
        if self._sc is None:
            self._sc = StorageClass()
        return self._sc

    def list_blockdevices(self, namespace):
        return self.blockdevice.list(namespace)

    def get_blockdevice(self, name, namespace):
        return self.blockdevice.get(name, namespace)

    def list_large_blockdevices(self, namespace):
        blockdevices = self.list_blockdevices(namespace)
        large_blockdevices = []

        logging(f"Finding blockdevices in namespace {namespace} >= {LARGE_DISK_BYTE} bytes")
        for blockdevice in blockdevices:
            try:
                size_bytes = int(
                    blockdevice.get("status", {})
                    .get("deviceStatus", {})
                    .get("capacity", {})
                    .get("sizeBytes")
                )
            except Exception:
                size_bytes = 0
                logging(
                    f"Unable to parse blockdevice sizeBytes for {blockdevice}", level="WARNING"
                )

            if size_bytes >= LARGE_DISK_BYTE:
                large_blockdevices.append(blockdevice)

        logging(f"Found {len(large_blockdevices)} large blockdevices in namespace {namespace}")
        return large_blockdevices

    def pick_unprovisioned_data_disks(self, namespace: str) -> dict:
        standard_node_names = self.host.get_standard_nodes()
        logging(f"Standard nodes: {standard_node_names}")

        large_disks = self.list_large_blockdevices(namespace)
        unprovisioned_disk_by_node = {}
        for blockdevice in large_disks:
            node_name = blockdevice.get("spec", {}).get("nodeName")
            if not node_name or node_name not in standard_node_names:
                continue
            if node_name in unprovisioned_disk_by_node:
                continue

            disk_name = blockdevice.get("metadata", {}).get("name")
            if not disk_name:
                continue

            disk_provision_phase = blockdevice.get("status", {}).get("provisionPhase")
            if disk_provision_phase != "Unprovisioned":
                continue

            unprovisioned_disk_by_node[node_name] = disk_name

        logging(f"Picked unprovisioned data disks: {unprovisioned_disk_by_node}")
        return unprovisioned_disk_by_node

    def provision_longhorn_storage(self, disk_name: str, engine_version: str, namespace: str):
        self.blockdevice.provision_longhorn_storage(disk_name, engine_version, namespace)

    def is_blockdevice_provisioned(self, name: str, namespace: str) -> bool:
        blockdevice = self.get_blockdevice(name, namespace)
        provision_phase = blockdevice and blockdevice.get("status", {}).get("provisionPhase")
        state = blockdevice and blockdevice.get("status", {}).get("state")

        if provision_phase == "Provisioned" and state == "Active":
            return True
        return False

    def get_lh_node(self, node_name: str):
        return self.host.get_lh_node(node_name)

    def get_lh_node_disk_status(self, node_name: str, disk_name: str):
        lh_node = self.get_lh_node(node_name)
        disk_status = lh_node.get("status", {}).get("diskStatus", {}).get(disk_name, {})
        return disk_status

    def get_lh_node_disk_status_condition(self, node_name, disk_name, condition_type):
        disk_status = self.get_lh_node_disk_status(node_name, disk_name)
        for condition in disk_status.get("conditions", []):
            if condition.get("type") == condition_type:
                return condition.get("status")

    # LVM-specific methods
    def identify_lvm_suitable_disks(self, min_size_gib):
        """Identify disks suitable for LVM on all nodes (>= min_size_gib GiB)"""
        logging(f'Identifying LVM-suitable disks >= {min_size_gib} GiB')
        return self.blockdevice.identify_lvm_suitable(int(min_size_gib))

    def create_lvm_volume_groups(self, disk_by_node, vg_type):
        """Create volume groups from identified disks"""
        logging(f'Creating LVM volume groups from {disk_by_node} type={vg_type}')
        return self.blockdevice.create_lvm_volume_groups(dict(disk_by_node), str(vg_type))

    def get_node_for_vg(self, vg_name, vg_node_map):
        """Get the node associated with a volume group"""
        node = dict(vg_node_map).get(vg_name, "")
        logging(f'Node for VG {vg_name}: {node}')
        return node

    def create_lvm_storage_class(self, sc_name, vg_name, vg_type, node):
        """Create an LVM StorageClass"""
        logging(f'Creating LVM StorageClass {sc_name} vg={vg_name} type={vg_type} node={node}')
        return self.sc.create_lvm_sc(sc_name, vg_name, vg_type, node)

    def delete_lvm_storage_class(self, sc_name):
        """Delete an LVM StorageClass"""
        logging(f'Deleting LVM StorageClass {sc_name}')
        return self.sc.delete(sc_name)

    def cleanup_lvm_volume_groups(self, disk_by_node):
        """Remove LVM volume groups from disks"""
        logging(f'Cleaning up LVM volume groups for {disk_by_node}')
        return self.blockdevice.cleanup_lvm_volume_groups(dict(disk_by_node))
