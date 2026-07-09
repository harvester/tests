"""
Snapshot CRD implementation
"""

import time

from kubernetes import client
from kubernetes.client.rest import ApiException
from utility.utility import logging, get_retry_count_and_interval
from snapshot.base import Base
from constant import (
    DEFAULT_NAMESPACE, DEFAULT_TIMEOUT_SHORT, HARVESTER_API_GROUP, HARVESTER_API_VERSION,
    KUBEVIRT_API_GROUP, VIRTUALMACHINEBACKUP_PLURAL
)
from crd import create_cr, delete_cr


class CRD(Base):

    def __init__(self):
        self.obj_api = client.CustomObjectsApi()
        self.retry_count, self.retry_interval = (
            get_retry_count_and_interval()
        )

    def _create_snapshot(self, namespace, snapshot_name, vm_name):
        try:
            body = {
                "apiVersion": f"{HARVESTER_API_GROUP}/{HARVESTER_API_VERSION}",
                "kind": "VirtualMachineBackup",
                "metadata": {
                    "name": f"{snapshot_name}",
                    "namespace": f"{namespace}",
                },
                "spec": {
                    "source": {
                        "apiGroup": f"{KUBEVIRT_API_GROUP}",
                        "kind": "VirtualMachine",
                        "name": f"{vm_name}"
                    },
                    "type": "snapshot"
                }
            }
            create_cr(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                plural=VIRTUALMACHINEBACKUP_PLURAL,
                namespace=namespace,
                body=body
            )
        except ApiException as err:
            logging(f"failed to create snapshot {namespace}/{snapshot_name}: {err}")
            raise
        self._wait_for_ready(namespace, snapshot_name)

    def _delete_snapshot(self, namespace, snapshot_name):
        try:
            delete_cr(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                plural=VIRTUALMACHINEBACKUP_PLURAL,
                namespace=namespace,
                name=snapshot_name
            )
        except ApiException as err:
            logging(f"failed to delete snapshot {namespace}/{snapshot_name}: {err}")
            raise
        self._wait_for_deleted(namespace, snapshot_name)

    def _wait_for_ready(self, namespace, snapshot_name, timeout=DEFAULT_TIMEOUT_SHORT):

        endtime = time.time() + timeout
        last_log_time = time.time()

        for _ in range(self.retry_count):
            try:
                snap = self.obj_api.get_namespaced_custom_object(
                    group=HARVESTER_API_GROUP,
                    version=HARVESTER_API_VERSION,
                    plural=VIRTUALMACHINEBACKUP_PLURAL,
                    namespace=namespace,
                    name=snapshot_name
                )
                conditions = snap.get('status', {}).get('conditions', [])
                for cond in conditions:
                    if cond.get('type', '') == "Ready" and cond.get('status', 'False') == "True":
                        return True

                now = time.time()
                if now - last_log_time >= 30:
                    logging(f"waiting for snapshot {namespace}/{snapshot_name} to be ready")
                    last_log_time = now

            except ApiException as err:
                if err.status != 404:
                    logging(f"error checking snapshot {namespace}/{snapshot_name}: {err}")
                    raise
            finally:
                if time.time() > endtime:
                    raise AssertionError(
                        f"Snapshot {namespace}/{snapshot_name} not ready within {timeout}s"
                    )
                time.sleep(self.retry_interval)

        raise AssertionError(
            f"Snapshot {namespace}/{snapshot_name} not ready after {self.retry_count} attempts"
        )

    def _wait_for_deleted(self, namespace, snapshot_name, timeout=DEFAULT_TIMEOUT_SHORT):
        endtime = time.time() + timeout
        last_log_time = time.time()

        for _ in range(self.retry_count):
            try:
                _ = self.obj_api.get_namespaced_custom_object(
                    group=HARVESTER_API_GROUP,
                    version=HARVESTER_API_VERSION,
                    plural=VIRTUALMACHINEBACKUP_PLURAL,
                    namespace=namespace,
                    name=snapshot_name
                )
                now = time.time()
                if now - last_log_time >= 30:
                    logging(f"waiting for snapshot {namespace}/{snapshot_name} to be deleted")
                    last_log_time = now
            except ApiException as err:
                if err.status == 404:
                    return True
                logging(f"error checing snapshot {namespace}/{snapshot_name}: {err}")
            finally:
                if time.time() > endtime:
                    raise AssertionError(
                        f"failed to delete snapshot {namespace}/{snapshot_name} within {timeout}s"
                    )
                time.sleep(self.retry_interval)
        raise AssertionError(
            f"snapshot {namespace}/{snapshot_name} not deleted after {self.retry_count} attempts"
        )

    def create(self, vm_name, snapshot_name, **kwargs):
        namespace = kwargs.get('namespace', DEFAULT_NAMESPACE)
        try:
            logging(f"Creating VM Snapshot {namespace}/{snapshot_name} for VM {vm_name}")
            self._create_snapshot(namespace, snapshot_name, vm_name)
            logging(
                f"Successfully created VM Snapshot {namespace}/{snapshot_name} for VM {vm_name}"
            )
        except ApiException as err:
            logging(f"failed to create snapshot {namespace}/{snapshot_name}: {err}")
            raise
        return {'metadata': {'name': snapshot_name, 'namespace': namespace}}

    def delete(self, snapshot_name, **kwargs):
        namespace = kwargs.get('namespace', DEFAULT_NAMESPACE)
        try:
            logging(f"Deleting VM Snapshot {namespace}/{snapshot_name}")
            self._delete_snapshot(namespace, snapshot_name)
            logging(f"Successfully deleted VM Snapshot {namespace}/{snapshot_name}")
        except ApiException as err:
            logging(f"failed to delete snapshot {namespace}/{snapshot_name}: {err}")
            raise
        return {'metadata': {'name': snapshot_name, 'namespace': namespace}}

    def wait_ready(self, snapshot_name, **kwargs):
        namespace = kwargs.get('namespace', DEFAULT_NAMESPACE)
        self._wait_for_ready(namespace, snapshot_name)

    def wait_deleted(self, snapshot_name, **kwargs):
        namespace = kwargs.get('namespace', DEFAULT_NAMESPACE)
        self._wait_for_deleted(namespace, snapshot_name)
