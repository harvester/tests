""" Backup Component: CRD Implementation

Layer 4: Component and its implementation

Backups and restores are managed through the Harvester CRDs
VirtualMachineBackup and VirtualMachineRestore (harvesterhci.io/v1beta1).
"""
import time

from crd import get_cr, create_cr, delete_cr, list_cr, wait_for_cr_deleted
from constant import (
    HARVESTER_API_GROUP, HARVESTER_API_VERSION,
    KUBEVIRT_API_GROUP,
    LONGHORN_API_GROUP, LONGHORN_API_VERSION, LONGHORN_NAMESPACE,
    VIRTUALMACHINEBACKUP_PLURAL, VIRTUALMACHINERESTORE_PLURAL,
    VIRTUALMACHINEIMAGE_PLURAL,
    BACKUPVOLUME_PLURAL, BACKUPBACKINGIMAGE_PLURAL, BACKING_IMAGE_PREFIX,
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

    def get_backup_volume_names(self, backup_name, namespace=DEFAULT_NAMESPACE):
        """Return the Longhorn volume names recorded in the backup's
        status.volumeBackups.

        The longhorn volume name (pvc-<uid>, what BackupVolume.spec.volumeName
        references) lives in the snapshotted PVC spec:
        volumeBackups[].persistentVolumeClaim.spec.volumeName — the top-level
        volumeBackups[].volumeName is the VM disk name (e.g. rootdisk) and is
        useless here. This mapping only exists while the VirtualMachineBackup
        is present (the source PVCs may already be gone after a
        replace-restore), so capture it BEFORE deleting the backup.
        """
        backup = self.get(backup_name, namespace)
        volume_backups = backup.get('status', {}).get('volumeBackups', [])
        names = []
        for vb in volume_backups:
            pv_name = (vb.get('persistentVolumeClaim', {})
                       .get('spec', {}).get('volumeName'))
            if pv_name:
                names.append(pv_name)
            else:
                logging(f"volumeBackup {vb.get('name')} has no PV name in its "
                        f"PVC spec; skipping", "WARNING")
        return names

    def cleanup_longhorn_backup_artifacts(self, volume_names, image_name,
                                          namespace=DEFAULT_NAMESPACE):
        """Delete the Longhorn bookkeeping CRs left on the backup target after
        the VirtualMachineBackup is deleted: BackupVolume (one per backed-up
        volume) and BackupBackingImage (the VM image's backing image copy).

        Deleting these CRs makes Longhorn remove the corresponding data from
        the backup store via finalizers. Parallel-safe: only CRs matching the
        given volume names / this image are touched. Must run while the image
        CR still exists (the UID-style backing image name needs it).
        """
        for bv in self._list_longhorn_cr(BACKUPVOLUME_PLURAL):
            name = bv['metadata']['name']
            # Newer longhorn uses a random CR name with spec.volumeName;
            # older versions name the CR after the volume itself.
            volume = bv.get('spec', {}).get('volumeName') or name
            if volume in volume_names:
                logging(f"Deleting longhorn BackupVolume {name} "
                        f"(volume {volume})")
                delete_cr(LONGHORN_API_GROUP, LONGHORN_API_VERSION,
                          LONGHORN_NAMESPACE, BACKUPVOLUME_PLURAL, name)

        candidates = self._backing_image_candidates(image_name, namespace)
        for bbi in self._list_longhorn_cr(BACKUPBACKINGIMAGE_PLURAL):
            name = bbi['metadata']['name']
            backing = bbi.get('spec', {}).get('backingImage') or name
            if backing in candidates:
                logging(f"Deleting longhorn BackupBackingImage {name} "
                        f"(backing image {backing})")
                delete_cr(LONGHORN_API_GROUP, LONGHORN_API_VERSION,
                          LONGHORN_NAMESPACE, BACKUPBACKINGIMAGE_PLURAL, name)

    def _list_longhorn_cr(self, plural):
        result = list_cr(LONGHORN_API_GROUP, LONGHORN_API_VERSION,
                         LONGHORN_NAMESPACE, plural)
        return result.get('items', [])

    def _backing_image_candidates(self, image_name, namespace):
        """Possible longhorn BackingImage names for a Harvester image:
        legacy '{namespace}-{name}' and UID-style 'vmi-{uid}'.
        """
        candidates = {f"{namespace}-{image_name}"}
        try:
            image = get_cr(HARVESTER_API_GROUP, HARVESTER_API_VERSION,
                           namespace, VIRTUALMACHINEIMAGE_PLURAL, image_name)
            uid = image.get('metadata', {}).get('uid')
            if uid:
                candidates.add(f"{BACKING_IMAGE_PREFIX}-{uid}")
        except Exception as e:
            logging(f"Could not resolve backing image UID for {image_name}: {e}",
                    "WARNING")
        return candidates
