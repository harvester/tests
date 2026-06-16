""" Blockdevice Component: CRD Implementation

Layer 4: Component and its implementation
"""

import random
import time
from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import get_cr, patch_cr
from constant import (
    HARVESTER_API_GROUP, HARVESTER_API_VERSION,
    DEFAULT_TIMEOUT, GIBIBYTE,
    LONGHORN_SYSTEM_NAMESPACE, LVM_VG_DM_THIN, LVM_VG_STRIPED,
)
from utility.utility import logging, get_retry_count_and_interval
from .base import Base


class CRD(Base):
    """CRD implementation for Blockdevice operations using Kubernetes API"""

    def __init__(self):
        """Initialize Kubernetes client"""
        self.core_api = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.common_parameters = {
            "group": HARVESTER_API_GROUP,
            "version": HARVESTER_API_VERSION,
            "plural": "blockdevices"
        }
        self.port_forward_process = None
        _, self.retry_interval = get_retry_count_and_interval()

    def list(self, namespace):
        try:
            return self.custom_api.list_namespaced_custom_object(
                **self.common_parameters,
                namespace=namespace
            ).get("items", [])
        except ApiException as e:
            if e.status == 404:
                logging(f"No blockdevice under {namespace}", level='WARNING')
                return []
            raise Exception(f"Failed to list blockdevices under {namespace}: {e}")

    def get(self, name, namespace):
        try:
            return get_cr(
                **self.common_parameters,
                namespace=namespace,
                name=name
            )
        except ApiException as e:
            if e.status == 404:
                raise Exception(f"Blockdevice {namespace}/{name} not found", level='ERROR')
            raise Exception(f"Failed to get blockdevice: {e}")

    def provision_longhorn_storage(self, name, engine_version, namespace):
        blockdevice = self.get(name, namespace)
        if not blockdevice:
            raise Exception(f"Blockdevice {namespace}/{name} not found")

        patch_body = {
            "spec": {
                "provision": True,
                "provisioner": {
                    "longhorn": {
                        "diskDriver": "auto",
                        "engineVersion": engine_version
                    }
                }
            }
        }
        try:
            patch_cr(
                **self.common_parameters,
                namespace=namespace,
                name=name,
                body=patch_body
            )
        except ApiException as e:
            raise Exception(f"Failed to provision blockdevice {namespace}/{name}: {e}")

    def identify_lvm_suitable(self, min_size_gib):
        """Identify blockdevices >= min_size_gib suitable for LVM.
        Returns dict {node_name: disk_name} with one disk per node.
        """
        min_size_bytes = int(min_size_gib) * GIBIBYTE

        blockdevices = self.custom_api.list_namespaced_custom_object(
            group=HARVESTER_API_GROUP,
            version=HARVESTER_API_VERSION,
            namespace=LONGHORN_SYSTEM_NAMESPACE,
            plural="blockdevices"
        ).get("items", [])

        disk_by_node = {}
        for bd in blockdevices:
            node_name = bd.get("spec", {}).get("nodeName", "")
            if not node_name:
                continue

            if bd.get("status", {}).get("provisionPhase", "") == "Provisioned":
                continue

            try:
                size_bytes = int(
                    bd.get("status", {})
                    .get("deviceStatus", {})
                    .get("capacity", {})
                    .get("sizeBytes", 0)
                )
            except (ValueError, TypeError):
                size_bytes = 0

            if size_bytes < min_size_bytes:
                continue

            if node_name not in disk_by_node:
                disk_name = bd.get("metadata", {}).get("name", "")
                if disk_name:
                    disk_by_node[node_name] = disk_name

        logging(f"Suitable disks for LVM: {disk_by_node}")
        return disk_by_node

    def create_lvm_volume_groups(self, disk_by_node, vg_type):
        """Create LVM volume groups on selected nodes.
        Single-node: creates the VG matching vg_type (dm-thin or striped).
        Multi-node: always creates vg-dm-thin + vg-dm-striped on separate nodes.
        Returns dict {vg_name: node_name}.
        """
        _VG_TYPE_MAP = {
            "dm-thin": LVM_VG_DM_THIN,
            "striped": LVM_VG_STRIPED,
        }
        nodes = list(disk_by_node.keys())
        if not nodes:
            raise AssertionError("No nodes with suitable disks found for LVM")

        vg_node_map = {}

        if len(nodes) >= 2:
            selected = random.sample(nodes, 2)
        else:
            selected = nodes[:1]

        node1 = selected[0]
        single_vg = _VG_TYPE_MAP.get(vg_type, LVM_VG_DM_THIN)
        self.provision_lvm_disk(disk_by_node[node1], node1, single_vg)
        vg_node_map[single_vg] = node1
        logging(f"Assigned {single_vg} to node {node1}")

        if len(selected) >= 2:
            node2 = selected[1]
            self.provision_lvm_disk(disk_by_node[node2], node2, LVM_VG_STRIPED)
            vg_node_map[LVM_VG_STRIPED] = node2
            logging(f"Assigned {LVM_VG_STRIPED} to node {node2}")

        self.wait_for_vgs_active(vg_node_map)
        return vg_node_map

    def provision_lvm_disk(self, disk_name, node_name, vg_name):
        """Provision a blockdevice for LVM with specified volume group"""
        logging(f"Provisioning disk {disk_name} on {node_name} for VG {vg_name}")
        patch_body = {
            "spec": {
                "provision": True,
                "provisioner": {
                    "lvm": {
                        "vgName": vg_name
                    }
                }
            }
        }
        try:
            patch_cr(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                namespace=LONGHORN_SYSTEM_NAMESPACE,
                plural="blockdevices",
                name=disk_name,
                body=patch_body
            )
        except ApiException as e:
            raise Exception(f"Failed to provision disk {disk_name} for VG {vg_name}: {e}")

    def wait_for_vgs_active(self, vg_node_map, timeout=DEFAULT_TIMEOUT):
        """Wait for all volume groups in vg_node_map to become active"""
        endtime = time.time() + timeout
        for vg_name, node_name in vg_node_map.items():
            while time.time() < endtime:
                try:
                    blockdevices = self.custom_api.list_namespaced_custom_object(
                        group=HARVESTER_API_GROUP,
                        version=HARVESTER_API_VERSION,
                        namespace=LONGHORN_SYSTEM_NAMESPACE,
                        plural="blockdevices"
                    ).get("items", [])

                    for bd in blockdevices:
                        bd_node = bd.get("spec", {}).get("nodeName", "")
                        bd_vg = (bd.get("spec", {}).get("provisioner", {})
                                 .get("lvm", {}).get("vgName", ""))
                        if bd_node == node_name and bd_vg == vg_name:
                            phase = bd.get("status", {}).get("provisionPhase", "")
                            state = bd.get("status", {}).get("state", "")
                            if phase == "Provisioned" and state == "Active":
                                logging(f"VG {vg_name} on {node_name} is active")
                                break
                    else:
                        time.sleep(self.retry_interval)
                        continue
                    break
                except ApiException:
                    time.sleep(self.retry_interval)
            else:
                raise AssertionError(f"VG {vg_name} on {node_name} not active within {timeout}s")

    def cleanup_lvm_volume_groups(self, disk_by_node):
        """Remove LVM provisioning from disks"""
        for node, disk_name in disk_by_node.items():
            try:
                patch_body = {"spec": {"provision": False, "provisioner": {}}}
                patch_cr(
                    group=HARVESTER_API_GROUP,
                    version=HARVESTER_API_VERSION,
                    namespace=LONGHORN_SYSTEM_NAMESPACE,
                    plural="blockdevices",
                    name=disk_name,
                    body=patch_body
                )
                logging(f"Cleaned up LVM provisioning for disk {disk_name} on {node}")
            except ApiException as e:
                logging(f"Error cleaning up disk {disk_name}: {e}")
