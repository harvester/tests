# flake8: noqa: F405
"""
Volume CRD Implementation - uses Kubernetes PersistentVolumeClaim for volume operations
"""
import time
from kubernetes import client
from kubernetes.client.rest import ApiException
from constant import (
    DEFAULT_NAMESPACE, DEFAULT_STORAGE_CLASS,
    VOLUME_STATE_BOUND,
    ACCESS_MODE_RWO,
    LABEL_TEST, LABEL_TEST_VALUE,
    DEFAULT_TIMEOUT_SHORT
)
from utility.utility import logging, get_retry_count_and_interval
from volume.base import Base


class CRD(Base):
    """
    Volume CRD implementation - uses Kubernetes PersistentVolumeClaim (PVC) resources
    """

    def __init__(self):
        self.core_api = client.CoreV1Api()
        self.retry_count, self.retry_interval = get_retry_count_and_interval()

    def create(self, volume_name, size, numberOfReplicas, frontend, **kwargs):
        """
        Create a PersistentVolumeClaim

        Note: Harvester uses Longhorn for storage, which is provisioned via StorageClass
        """
        namespace = kwargs.get('namespace', DEFAULT_NAMESPACE)
        storage_class = kwargs.get('storage_class', DEFAULT_STORAGE_CLASS)
        access_mode = kwargs.get('access_mode', ACCESS_MODE_RWO)

        # Build PVC manifest
        body = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": volume_name,
                "namespace": namespace,
                "labels": {
                    LABEL_TEST: LABEL_TEST_VALUE
                },
                "annotations": {
                    "volume.kubernetes.io/storage-provisioner": "driver.longhorn.io"    # Noqa
                }
            },
            "spec": {
                "accessModes": [access_mode],
                "storageClassName": storage_class,
                "resources": {
                    "requests": {
                        "storage": size
                    }
                }
            }
        }

        # Add Longhorn-specific parameters
        if numberOfReplicas:
            if 'annotations' not in body['metadata']:
                body['metadata']['annotations'] = {}
            body['metadata']['annotations'][
                'longhorn.io/number-of-replicas'
            ] = str(numberOfReplicas)

        try:
            logging(f"Creating PersistentVolumeClaim {namespace}/{volume_name}")
            pvc = self.core_api.create_namespaced_persistent_volume_claim(
                namespace=namespace,
                body=body
            )

            # Wait for PVC to be created
            self.wait_for_volume_created(volume_name, namespace)

            return {
                'metadata': {
                    'name': pvc.metadata.name,
                    'namespace': pvc.metadata.namespace
                },
                'status': {
                    'phase': pvc.status.phase if pvc.status else 'Pending'
                }
            }

        except ApiException as e:
            logging(f"Failed to create PVC {volume_name}: {e}")
            raise Exception(f"Failed to create volume: {e.status}, {e.reason}")

    def delete(self, volume_name, wait=True):
        """Delete a PersistentVolumeClaim"""
        namespace = DEFAULT_NAMESPACE

        try:
            logging(f"Deleting PersistentVolumeClaim {namespace}/{volume_name}")
            self.core_api.delete_namespaced_persistent_volume_claim(
                name=volume_name,
                namespace=namespace
            )

            if wait:
                self.wait_for_deleted(volume_name)

        except ApiException as e:
            if e.status != 404:  # Ignore not found errors
                logging(f"Error deleting PVC {volume_name}: {e}")
                raise

    def get(self, volume_name, namespace=DEFAULT_NAMESPACE):
        """Get a PersistentVolumeClaim"""
        try:
            pvc = self.core_api.read_namespaced_persistent_volume_claim(
                name=volume_name,
                namespace=namespace
            )

            return {
                'metadata': {
                    'name': pvc.metadata.name,
                    'namespace': pvc.metadata.namespace,
                    'labels': pvc.metadata.labels or {},
                    'annotations': pvc.metadata.annotations or {}
                },
                'spec': {
                    'accessModes': pvc.spec.access_modes or [],
                    'storageClassName': pvc.spec.storage_class_name,
                    'resources': {
                        'requests': {
                            'storage': (
                                pvc.spec.resources.requests.get('storage')
                                if pvc.spec.resources else None
                            )
                        }
                    }
                },
                'status': {
                    'phase': pvc.status.phase if pvc.status else 'Unknown',
                    'capacity': (
                        dict(pvc.status.capacity)
                        if pvc.status and pvc.status.capacity else {}
                    )
                }
            }
        except ApiException as e:
            logging(f"Failed to get PVC {volume_name}: {e}")
            raise

    def list(self, namespace=DEFAULT_NAMESPACE, label_selector=None):
        """List PersistentVolumeClaims"""
        try:
            pvcs = self.core_api.list_namespaced_persistent_volume_claim(
                namespace=namespace,
                label_selector=label_selector
            )

            result = []
            for pvc in pvcs.items:
                result.append({
                    'metadata': {
                        'name': pvc.metadata.name,
                        'namespace': pvc.metadata.namespace
                    },
                    'status': {
                        'phase': pvc.status.phase if pvc.status else 'Unknown'
                    }
                })

            return result
        except ApiException as e:
            logging(f"Failed to list PVCs: {e}")
            raise

    def attach(self, volume_name, node_name):
        """
        Attach volume to node
        Note: PVCs are automatically attached when used by a pod
        This is a no-op for PVCs
        """
        logging("PVCs are attached automatically when used by pods")
        pass

    def detach(self, volume_name):
        """
        Detach volume
        Note: PVCs are automatically detached when pod is deleted
        This is a no-op for PVCs
        """
        logging("PVCs are detached automatically when pods are deleted")
        pass

    def wait_for_volume_created(self, volume_name, namespace=DEFAULT_NAMESPACE):
        """Wait for PVC to be created"""
        for i in range(self.retry_count):
            try:
                self.get(volume_name, namespace)
                logging(f"PVC {namespace}/{volume_name} created")
                return True
            except Exception:
                logging(f"Waiting for PVC to be created ({i})...")
                time.sleep(self.retry_interval)

        raise AssertionError(f"PVC {namespace}/{volume_name} not created")

    def wait_for_running(self, volume_name, timeout=DEFAULT_TIMEOUT_SHORT):
        """Wait for volume to be bound"""
        return self.wait_for_attached(volume_name, timeout)

    def wait_for_attached(self, volume_name, timeout=DEFAULT_TIMEOUT_SHORT):
        """Wait for PVC to be bound"""
        namespace = DEFAULT_NAMESPACE
        endtime = time.time() + timeout

        while time.time() < endtime:
            try:
                pvc = self.get(volume_name, namespace)
                phase = pvc.get('status', {}).get('phase')

                if phase == VOLUME_STATE_BOUND:
                    logging(f"PVC {namespace}/{volume_name} is bound")
                    return True

                logging(f"Waiting for PVC to be bound (current phase: {phase})...")

            except Exception as e:
                logging(f"Error checking PVC status: {e}")

            time.sleep(self.retry_interval)

        raise AssertionError(f"PVC {namespace}/{volume_name} did not bind within {timeout}s")

    def wait_for_deleted(self, volume_name, timeout=DEFAULT_TIMEOUT_SHORT):
        """Wait for PVC to be deleted"""
        namespace = DEFAULT_NAMESPACE
        endtime = time.time() + timeout

        while time.time() < endtime:
            try:
                self.get(volume_name, namespace)
                logging("Waiting for PVC to be deleted...")
            except ApiException as e:
                if e.status == 404:
                    logging(f"PVC {namespace}/{volume_name} deleted")
                    return True

            time.sleep(self.retry_interval)

        raise AssertionError(f"PVC {namespace}/{volume_name} was not deleted within {timeout}s")

    def get_status(self, volume_name):
        """Get volume status"""
        pvc = self.get(volume_name)
        status = pvc.get('status', {})

        return {
            'state': status.get('phase', 'Unknown'),
            'capacity': status.get('capacity', {}),
            'access_modes': pvc.get('spec', {}).get('accessModes', [])
        }

    def expand(self, volume_name, new_size):
        """
        Expand volume size
        This requires patching the PVC spec.resources.requests.storage
        """
        namespace = DEFAULT_NAMESPACE

        try:
            # Patch PVC to increase size
            body = {
                "spec": {
                    "resources": {
                        "requests": {
                            "storage": new_size
                        }
                    }
                }
            }

            self.core_api.patch_namespaced_persistent_volume_claim(
                name=volume_name,
                namespace=namespace,
                body=body
            )

            logging(f"PVC {namespace}/{volume_name} expanded to {new_size}")
        except ApiException as e:
            logging(f"Failed to expand PVC: {e}")
            raise

    def create_snapshot(self, volume_name, snapshot_name):
        """
        Create volume snapshot
        Note: This uses VolumeSnapshot CRD
        """
        namespace = DEFAULT_NAMESPACE

        body = {
            "apiVersion": "snapshot.storage.k8s.io/v1",
            "kind": "VolumeSnapshot",
            "metadata": {
                "name": snapshot_name,
                "namespace": namespace
            },
            "spec": {
                "source": {
                    "persistentVolumeClaimName": volume_name
                }
            }
        }

        try:
            obj_api = client.CustomObjectsApi()
            obj_api.create_namespaced_custom_object(
                group="snapshot.storage.k8s.io",
                version="v1",
                namespace=namespace,
                plural="volumesnapshots",
                body=body
            )

            logging(f"VolumeSnapshot {namespace}/{snapshot_name} created")
        except ApiException as e:
            logging(f"Failed to create snapshot: {e}")
            raise

    def delete_snapshot(self, volume_name, snapshot_name):
        """Delete volume snapshot"""
        namespace = DEFAULT_NAMESPACE

        try:
            obj_api = client.CustomObjectsApi()
            obj_api.delete_namespaced_custom_object(
                group="snapshot.storage.k8s.io",
                version="v1",
                namespace=namespace,
                plural="volumesnapshots",
                name=snapshot_name
            )

            logging(f"VolumeSnapshot {namespace}/{snapshot_name} deleted")
        except ApiException as e:
            if e.status != 404:
                logging(f"Failed to delete snapshot: {e}")
                raise

    def restore_from_snapshot(self, volume_name, snapshot_name, new_volume_name):
        """Restore volume from snapshot"""
        namespace = DEFAULT_NAMESPACE
        storage_class = DEFAULT_STORAGE_CLASS

        # Get original volume to get size
        original_pvc = self.get(volume_name, namespace)
        size = original_pvc['spec']['resources']['requests']['storage']

        # Create new PVC from snapshot
        body = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": new_volume_name,
                "namespace": namespace
            },
            "spec": {
                "accessModes": [ACCESS_MODE_RWO],
                "storageClassName": storage_class,
                "resources": {
                    "requests": {
                        "storage": size
                    }
                },
                "dataSource": {
                    "name": snapshot_name,
                    "kind": "VolumeSnapshot",
                    "apiGroup": "snapshot.storage.k8s.io"
                }
            }
        }

        try:
            self.core_api.create_namespaced_persistent_volume_claim(
                namespace=namespace,
                body=body
            )

            logging(f"PVC {namespace}/{new_volume_name} created from snapshot {snapshot_name}")
        except ApiException as e:
            logging(f"Failed to restore from snapshot: {e}")
            raise

    def cleanup(self):
        """Clean up all test volumes"""
        logging('Cleaning up test volumes')

        try:
            # List all PVCs with test label
            pvcs = self.list(
                namespace=DEFAULT_NAMESPACE,
                label_selector=f"{LABEL_TEST}={LABEL_TEST_VALUE}"
            )

            for pvc in pvcs:
                pvc_name = pvc['metadata']['name']
                namespace = pvc['metadata']['namespace']

                try:
                    logging(f'Deleting test PVC: {namespace}/{pvc_name}')
                    self.delete(pvc_name, wait=False)
                except Exception as e:
                    logging(f'Error deleting PVC {pvc_name}: {e}', "WARNING")
        except Exception as e:
            logging(f'Error during volume cleanup: {e}', 'WARNING')
