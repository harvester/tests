"""Snapshot Component: CRD Implementation
Layer 4: Component and its implementation
"""

import time
from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import create_cr, delete_cr
from constant import (
    HARVESTER_API_GROUP, HARVESTER_API_VERSION,
    KUBEVIRT_API_GROUP, KUBEVIRT_API_VERSION,
    DEFAULT_NAMESPACE, DEFAULT_TIMEOUT,
    LABEL_TEST, LABEL_TEST_VALUE,
)
from utility.utility import logging, get_retry_count_and_interval, generate_name_with_suffix
from .base import Base


class CRD(Base):
    """CRD implementation for VM Snapshot operations via Harvester VirtualMachineBackup"""

    def __init__(self):
        self.custom_api = client.CustomObjectsApi()
        _, self.retry_interval = get_retry_count_and_interval()

    def take_snapshot(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Take a VM snapshot via Harvester VirtualMachineBackup; returns snapshot_name"""
        snapshot_name = generate_name_with_suffix(vm_name, "snap")
        logging(f"Taking snapshot {snapshot_name} of VM {vm_name}")

        # Fetch VM UID for ownerReference (best-effort)
        try:
            vm = self.custom_api.get_namespaced_custom_object(
                group=KUBEVIRT_API_GROUP, version=KUBEVIRT_API_VERSION,
                namespace=namespace, plural="virtualmachines", name=vm_name
            )
            vm_uid = vm.get("metadata", {}).get("uid", "")
        except ApiException:
            vm_uid = ""

        body = {
            "apiVersion": f"{HARVESTER_API_GROUP}/{HARVESTER_API_VERSION}",
            "kind": "VirtualMachineBackup",
            "metadata": {
                "name": snapshot_name,
                "namespace": namespace,
                "labels": {LABEL_TEST: LABEL_TEST_VALUE},
                "ownerReferences": [{
                    "apiVersion": f"{KUBEVIRT_API_GROUP}/v1",
                    "kind": "VirtualMachine",
                    "name": vm_name,
                    "uid": vm_uid
                }]
            },
            "spec": {
                "type": "snapshot",
                "source": {
                    "apiGroup": KUBEVIRT_API_GROUP,
                    "kind": "VirtualMachine",
                    "name": vm_name
                }
            }
        }

        try:
            create_cr(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                namespace=namespace,
                plural="virtualmachinebackups",
                body=body
            )
        except ApiException as e:
            raise Exception(f"Failed to take snapshot of VM {vm_name}: {e}")

        self.wait_for_snapshot_ready(snapshot_name, namespace)
        return snapshot_name

    def wait_for_snapshot_ready(self, snapshot_name, namespace=DEFAULT_NAMESPACE,
                                timeout=DEFAULT_TIMEOUT):
        """Wait for a VirtualMachineBackup snapshot to be ready"""
        endtime = time.time() + timeout
        while time.time() < endtime:
            try:
                snap = self.custom_api.get_namespaced_custom_object(
                    group=HARVESTER_API_GROUP,
                    version=HARVESTER_API_VERSION,
                    namespace=namespace,
                    plural="virtualmachinebackups",
                    name=snapshot_name
                )
                if snap.get("status", {}).get("readyToUse", False):
                    logging(f"Snapshot {snapshot_name} is ready")
                    return
            except ApiException:
                pass
            time.sleep(self.retry_interval)

        raise AssertionError(f"Snapshot {snapshot_name} not ready within {timeout}s")

    def delete_snapshot(self, snapshot_name, namespace=DEFAULT_NAMESPACE):
        """Delete a VirtualMachineBackup snapshot"""
        try:
            delete_cr(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                namespace=namespace,
                plural="virtualmachinebackups",
                name=snapshot_name
            )
            logging(f"Snapshot {snapshot_name} deleted")
        except ApiException as e:
            if e.status != 404:
                logging(f"Error deleting snapshot {snapshot_name}: {e}")

    def restore_snapshot_to_new_vm(self, snapshot_name, new_vm_name,
                                   namespace=DEFAULT_NAMESPACE):
        """Restore a Harvester VirtualMachineBackup snapshot to a new VM"""
        restore_name = f"{new_vm_name}-restore"
        logging(f"Restoring snapshot {snapshot_name} to new VM {new_vm_name}")
        body = {
            "apiVersion": f"{HARVESTER_API_GROUP}/{HARVESTER_API_VERSION}",
            "kind": "VirtualMachineRestore",
            "metadata": {
                "name": restore_name,
                "namespace": namespace,
                "labels": {LABEL_TEST: LABEL_TEST_VALUE}
            },
            "spec": {
                "target": {
                    "apiGroup": KUBEVIRT_API_GROUP,
                    "kind": "VirtualMachine",
                    "name": new_vm_name
                },
                "virtualMachineBackupName": snapshot_name,
                "virtualMachineBackupNamespace": namespace,
                "newVM": True
            }
        }
        try:
            create_cr(group=HARVESTER_API_GROUP, version=HARVESTER_API_VERSION,
                      namespace=namespace, plural="virtualmachinerestores", body=body)
        except ApiException as e:
            raise Exception(f"Failed to restore snapshot to new VM: {e}")
        self._wait_for_restore_complete(restore_name, namespace)

    def restore_snapshot_to_existing_vm(self, snapshot_name, vm_name,
                                        namespace=DEFAULT_NAMESPACE):
        """Restore a Harvester VirtualMachineBackup snapshot to an existing (stopped) VM"""
        restore_name = f"{vm_name}-restore-{int(time.time())}"
        logging(f"Restoring snapshot {snapshot_name} to existing VM {vm_name}")
        body = {
            "apiVersion": f"{HARVESTER_API_GROUP}/{HARVESTER_API_VERSION}",
            "kind": "VirtualMachineRestore",
            "metadata": {
                "name": restore_name,
                "namespace": namespace,
                "labels": {LABEL_TEST: LABEL_TEST_VALUE}
            },
            "spec": {
                "target": {
                    "apiGroup": KUBEVIRT_API_GROUP,
                    "kind": "VirtualMachine",
                    "name": vm_name
                },
                "virtualMachineBackupName": snapshot_name,
                "virtualMachineBackupNamespace": namespace,
                "deletionPolicy": "retain"
            }
        }
        try:
            create_cr(group=HARVESTER_API_GROUP, version=HARVESTER_API_VERSION,
                      namespace=namespace, plural="virtualmachinerestores", body=body)
        except ApiException as e:
            raise Exception(f"Failed to restore snapshot to existing VM: {e}")
        self._wait_for_restore_complete(restore_name, namespace)

    def _wait_for_restore_complete(self, restore_name, namespace=DEFAULT_NAMESPACE,
                                   timeout=DEFAULT_TIMEOUT):
        """Poll until the Harvester VirtualMachineRestore reports complete"""
        endtime = time.time() + timeout
        while time.time() < endtime:
            try:
                restore = self.custom_api.get_namespaced_custom_object(
                    group=HARVESTER_API_GROUP, version=HARVESTER_API_VERSION,
                    namespace=namespace, plural="virtualmachinerestores", name=restore_name
                )
                if restore.get("status", {}).get("complete", False):
                    logging(f"Restore {restore_name} completed")
                    return
            except ApiException:
                pass
            time.sleep(self.retry_interval)
        raise AssertionError(f"Restore {restore_name} not complete within {timeout}s")
