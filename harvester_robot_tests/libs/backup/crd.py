""" Backup Component: CRD Implementation

Layer 4: Component and its implementation

Backups and restores are managed through the Harvester CRDs
VirtualMachineBackup and VirtualMachineRestore (harvesterhci.io/v1beta1).
"""
import time

from crd import get_cr, create_cr, delete_cr, wait_for_cr_deleted
from constant import (
    HARVESTER_API_GROUP, HARVESTER_API_VERSION,
    KUBEVIRT_API_GROUP,
    VIRTUALMACHINEBACKUP_PLURAL, VIRTUALMACHINERESTORE_PLURAL,
    BACKUP_TYPE_BACKUP, DELETION_POLICY_DELETE, DELETION_POLICY_RETAIN,
    DEFAULT_NAMESPACE, DEFAULT_TIMEOUT_LONG, DEFAULT_TIMEOUT_SHORT,
)
from utility.utility import logging, get_retry_count_and_interval
from backup.base import Base


class CRD(Base):
    """CRD implementation for VM backup/restore operations"""

    def __init__(self):
        super().__init__()
        self.retry_count, self.retry_interval = get_retry_count_and_interval()

    def create(self, vm_name, backup_name, namespace=DEFAULT_NAMESPACE):
        """Create a VirtualMachineBackup for the given VM"""
        logging(f"Creating VirtualMachineBackup {namespace}/{backup_name} "
                f"for VM {vm_name}")
        body = {
            "apiVersion": f"{HARVESTER_API_GROUP}/{HARVESTER_API_VERSION}",
            "kind": "VirtualMachineBackup",
            "metadata": {
                "name": backup_name,
                "namespace": namespace
            },
            "spec": {
                "type": BACKUP_TYPE_BACKUP,
                "source": {
                    "apiGroup": KUBEVIRT_API_GROUP,
                    "kind": "VirtualMachine",
                    "name": vm_name
                }
            }
        }
        return create_cr(
            HARVESTER_API_GROUP, HARVESTER_API_VERSION,
            namespace, VIRTUALMACHINEBACKUP_PLURAL, body
        )

    def get(self, backup_name, namespace=DEFAULT_NAMESPACE):
        """Get a VirtualMachineBackup by name"""
        return get_cr(
            HARVESTER_API_GROUP, HARVESTER_API_VERSION,
            namespace, VIRTUALMACHINEBACKUP_PLURAL, backup_name
        )

    def delete(self, backup_name, namespace=DEFAULT_NAMESPACE):
        """Delete a VirtualMachineBackup"""
        logging(f"Deleting VirtualMachineBackup {namespace}/{backup_name}")
        return delete_cr(
            HARVESTER_API_GROUP, HARVESTER_API_VERSION,
            namespace, VIRTUALMACHINEBACKUP_PLURAL, backup_name
        )

    def wait_for_ready(self, backup_name, timeout=DEFAULT_TIMEOUT_LONG,
                       namespace=DEFAULT_NAMESPACE):
        """Wait until the backup's status.readyToUse is true.

        Fails fast when the controller reports status.error.
        """
        endtime = time.time() + timeout
        last_log_time = 0
        status = {}

        while time.time() < endtime:
            try:
                backup = self.get(backup_name, namespace)
                status = backup.get('status', {})
            except Exception as e:
                logging(f"Error getting backup {backup_name}: {e}")
                status = {}

            if status.get('readyToUse'):
                logging(f"Backup {namespace}/{backup_name} is ready to use")
                return True

            error = status.get('error')
            if error:
                raise AssertionError(
                    f"Backup {namespace}/{backup_name} failed: "
                    f"{error.get('message', error)}"
                )

            now = time.time()
            if now - last_log_time >= 30:
                progress = status.get('progress', 0)
                logging(f"Waiting for backup {backup_name} to be ready "
                        f"(progress: {progress})...")
                last_log_time = now

            time.sleep(self.retry_interval)

        raise AssertionError(
            f"Backup {namespace}/{backup_name} was not ready within {timeout}s: "
            f"status={status}"
        )

    def wait_for_deleted(self, backup_name, timeout=DEFAULT_TIMEOUT_SHORT,
                         namespace=DEFAULT_NAMESPACE):
        """Wait for the backup CR to be removed"""
        wait_for_cr_deleted(
            HARVESTER_API_GROUP, HARVESTER_API_VERSION,
            namespace, VIRTUALMACHINEBACKUP_PLURAL, backup_name,
            timeout=timeout
        )

    def _create_restore(self, backup_name, restore_name, target_vm_name,
                        namespace, extra_spec):
        body = {
            "apiVersion": f"{HARVESTER_API_GROUP}/{HARVESTER_API_VERSION}",
            "kind": "VirtualMachineRestore",
            "metadata": {
                "name": restore_name,
                "namespace": namespace
            },
            "spec": {
                "target": {
                    "apiGroup": KUBEVIRT_API_GROUP,
                    "kind": "VirtualMachine",
                    "name": target_vm_name
                },
                "virtualMachineBackupName": backup_name,
                "virtualMachineBackupNamespace": namespace,
                **extra_spec
            }
        }
        return create_cr(
            HARVESTER_API_GROUP, HARVESTER_API_VERSION,
            namespace, VIRTUALMACHINERESTORE_PLURAL, body
        )

    def restore_to_new_vm(self, backup_name, restore_name, new_vm_name,
                          namespace=DEFAULT_NAMESPACE):
        """Restore a backup into a brand-new VM"""
        logging(f"Restoring backup {backup_name} to new VM "
                f"{namespace}/{new_vm_name} (restore: {restore_name})")
        return self._create_restore(
            backup_name, restore_name, new_vm_name, namespace,
            extra_spec={"newVM": True}
        )

    def restore_replace_vm(self, backup_name, restore_name, delete_volumes=True,
                           namespace=DEFAULT_NAMESPACE):
        """Restore a backup over its source VM (which must be stopped).

        The target VM name is taken from the backup's spec.source, matching
        what the dashboard does for "replace existing" restores.
        """
        backup = self.get(backup_name, namespace)
        target_vm_name = backup['spec']['source']['name']
        deletion_policy = (
            DELETION_POLICY_DELETE if delete_volumes else DELETION_POLICY_RETAIN
        )
        logging(f"Restoring backup {backup_name} replacing VM "
                f"{namespace}/{target_vm_name} "
                f"(restore: {restore_name}, deletionPolicy: {deletion_policy})")
        return self._create_restore(
            backup_name, restore_name, target_vm_name, namespace,
            extra_spec={"deletionPolicy": deletion_policy}
        )

    def wait_for_restore_completed(self, restore_name, timeout=DEFAULT_TIMEOUT_LONG,
                                   namespace=DEFAULT_NAMESPACE):
        """Wait until the restore's status.complete is true"""
        endtime = time.time() + timeout
        last_log_time = 0
        status = {}

        while time.time() < endtime:
            try:
                restore = get_cr(
                    HARVESTER_API_GROUP, HARVESTER_API_VERSION,
                    namespace, VIRTUALMACHINERESTORE_PLURAL, restore_name
                )
                status = restore.get('status', {})
            except Exception as e:
                logging(f"Error getting restore {restore_name}: {e}")
                status = {}

            if status.get('complete'):
                logging(f"Restore {namespace}/{restore_name} is complete")
                return True

            now = time.time()
            if now - last_log_time >= 30:
                conditions = status.get('conditions', [])
                logging(f"Waiting for restore {restore_name} to complete "
                        f"(conditions: {conditions})...")
                last_log_time = now

            time.sleep(self.retry_interval)

        raise AssertionError(
            f"Restore {namespace}/{restore_name} did not complete within "
            f"{timeout}s: status={status}"
        )

    def delete_restore(self, restore_name, namespace=DEFAULT_NAMESPACE):
        """Delete a VirtualMachineRestore (bookkeeping object cleanup)"""
        logging(f"Deleting VirtualMachineRestore {namespace}/{restore_name}")
        return delete_cr(
            HARVESTER_API_GROUP, HARVESTER_API_VERSION,
            namespace, VIRTUALMACHINERESTORE_PLURAL, restore_name
        )
