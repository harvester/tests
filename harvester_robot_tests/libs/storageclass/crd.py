""" StorageClass Component: CRD Implementation

Layer 4: Component and its implementation
"""

from kubernetes import client
from kubernetes.client.rest import ApiException
from utility.utility import logging
from constant import LABEL_TEST, LABEL_TEST_VALUE, LVM_PROVISIONER
from .base import Base

# CSI parameters a Longhorn encrypted StorageClass points at its key Secret with
ENCRYPTION_SECRET_PARAMS = (
    "provisioner", "node-publish", "node-stage", "node-expand",
)


class CRD(Base):
    """CRD implementation for StorageClass operations using Kubernetes API"""

    def __init__(self):
        super().__init__()
        self.custom_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()
        self.common_parameters = {
            "group": "storage.k8s.io",
            "version": "v1",
            "plural": "storageclasses"
        }

    def _normalize_disk_selector(self, disk_selector):
        if disk_selector is None:
            return ""
        parts = [part.strip() for part in str(disk_selector).split(",")]
        parts = [part for part in parts if part]
        return ",".join(parts)

    def create(self, name, data_engine, number_of_replicas, disk_selector,
               encryption_secret=None):
        if self.get(name):
            raise Exception(f"StorageClass {name} already exists")

        disk_selector_value = self._normalize_disk_selector(disk_selector)
        body = {
            "apiVersion": "storage.k8s.io/v1",
            "kind": "StorageClass",
            "metadata": {
                "name": name,
                "labels": {
                        LABEL_TEST: LABEL_TEST_VALUE
                }
            },
            "provisioner": "driver.longhorn.io",
            "allowVolumeExpansion": True,
            "reclaimPolicy": "Delete",
            "volumeBindingMode": "Immediate",
            "parameters": {
                "numberOfReplicas": str(number_of_replicas),
                "staleReplicaTimeout": "30",
                "encrypted": "false",
                "migratable": "true",
                "dataEngine": str(data_engine)
            }
        }

        # encryption_secret is "<namespace>/<name>" of a Secret created by
        # create_encryption_secret; Longhorn encrypts every volume of the SC
        if encryption_secret:
            secret_ns, secret_name = encryption_secret.split("/", 1)
            body["parameters"]["encrypted"] = "true"
            for prefix in ENCRYPTION_SECRET_PARAMS:
                key = f"csi.storage.k8s.io/{prefix}-secret"
                body["parameters"][f"{key}-name"] = secret_name
                body["parameters"][f"{key}-namespace"] = secret_ns

        # An empty diskSelector is read by Longhorn as the tag "", so omit it
        if disk_selector_value:
            body["parameters"]["diskSelector"] = disk_selector_value

        # The Harvester webhook rejects CDI annotations on a Longhorn v1
        # StorageClass ("longhorn v1 does not support CDI annotations");
        # only v2 needs the snapshot class for CDI-backed images.
        if str(data_engine) == "v2":
            body["metadata"]["annotations"] = {
                "cdi.harvesterhci.io/storageProfileVolumeSnapshotClass": "longhorn-snapshot"
            }

        try:
            return self.custom_api.create_cluster_custom_object(
                **self.common_parameters,
                body=body
            )
        except ApiException as e:
            raise Exception(f"Failed to create StorageClass {name}: {e}")

    def create_lvm(self, name, vg_name, vg_type, node):
        """Create a node-local StorageClass for the LVM CSI driver."""
        if self.get(name):
            raise Exception(f"StorageClass {name} already exists")
        body = {
            "apiVersion": "storage.k8s.io/v1",
            "kind": "StorageClass",
            "metadata": {"name": name, "labels": {LABEL_TEST: LABEL_TEST_VALUE}},
            "provisioner": LVM_PROVISIONER,
            "allowVolumeExpansion": True,
            "reclaimPolicy": "Delete",
            # Immediate is the interim decision for LVM: the SC is pinned to a
            # single node via allowedTopologies, so binding never needs the
            # consumer for placement, and WaitForFirstConsumer deadlocks the
            # Harvester VM-restore flow (VM start waits for volumes-ready
            # while a WFFC PVC waits for the VM's pod).
            "volumeBindingMode": "Immediate",
            "parameters": {"node": node, "vgName": vg_name, "type": vg_type},
            "allowedTopologies": [{
                "matchLabelExpressions": [{
                    "key": "topology.lvm.csi/node",
                    "values": [node],
                }],
            }],
        }
        return self.custom_api.create_cluster_custom_object(
            **self.common_parameters, body=body
        )

    def create_encryption_secret(self, name, namespace, passphrase):
        """Create the Secret holding the LUKS passphrase of encrypted volumes"""
        body = client.V1Secret(
            metadata=client.V1ObjectMeta(
                name=name, namespace=namespace,
                labels={LABEL_TEST: LABEL_TEST_VALUE}),
            string_data={
                "CRYPTO_KEY_VALUE": passphrase,
                "CRYPTO_KEY_PROVIDER": "secret",
                "CRYPTO_KEY_CIPHER": "aes-xts-plain64",
                "CRYPTO_KEY_HASH": "sha256",
                "CRYPTO_KEY_SIZE": "256",
                "CRYPTO_PBKDF": "argon2i",
            },
        )
        logging(f"Creating encryption Secret {namespace}/{name}")
        return self.core_api.create_namespaced_secret(namespace, body)

    def delete_encryption_secret(self, name, namespace):
        try:
            self.core_api.delete_namespaced_secret(name, namespace)
            logging(f"Deleted encryption Secret {namespace}/{name}")
        except ApiException as e:
            if e.status != 404:
                raise

    def delete(self, name):
        try:
            self.custom_api.delete_cluster_custom_object(
                **self.common_parameters,
                name=name
            )
            logging(f"Deleted StorageClass {name}")
        except ApiException as e:
            if e.status == 404:
                return False
            raise Exception(f"Failed to delete StorageClass {name}: {e}")
        return True

    def get(self, name):
        try:
            return self.custom_api.get_cluster_custom_object(
                **self.common_parameters,
                name=name
            )
        except ApiException as e:
            if e.status == 404:
                return None
            raise Exception(f"Failed to get StorageClass {name}: {e}")

    def list(self, label_selector=None):
        """List VirtualMachines."""
        result = self.custom_api.list_cluster_custom_object(
            **self.common_parameters,
            label_selector=label_selector
        )
        return result.get("items", [])

    def cleanup(self):
        try:
            scs = self.list(
                label_selector=f"{LABEL_TEST}={LABEL_TEST_VALUE}"
            )

            for sc in scs:
                try:
                    sc_name = sc['metadata']['name']
                    logging(f'Deleting storage class: {sc_name}')
                    self.delete(sc_name)
                except Exception as e:
                    logging(f'Error deleting storage class: {sc_name}: {e}', 'WARNING')
        except Exception as e:
            logging(f'Error during storage class cleanup: {e}', 'WARNING')
