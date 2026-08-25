
"""
Layer 3: LVM driver internals keywords - verification helpers that look
behind the CSI facade: snapshot handles, the driver's snapshot-location
ConfigMap records (harvester/csi-driver-lvm#64), backend LV presence on
nodes, and pre-provisioned VolumeSnapshotContent import. Kubernetes API
only; no Harvester REST equivalent exists, so no CRD/REST strategy split.
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))) # noqa E402
from kubernetes import client # noqa E402
from kubernetes.client.rest import ApiException # noqa E402
from kubernetes.stream import stream # noqa E402
from utility.utility import logging, init_k8s_api_client, get_retry_count_and_interval # noqa E402
from constant import DEFAULT_NAMESPACE # noqa E402

SNAPSHOT_GROUP = "snapshot.storage.k8s.io"
SNAPSHOT_VERSION = "v1"
LVM_DRIVER_NAME = "lvm.driver.harvesterhci.io"
LVM_DRIVER_NAMESPACE = os.getenv("LVM_DRIVER_NAMESPACE", "harvester-system")
# Introduced by harvester/csi-driver-lvm#64: one immutable ConfigMap per
# snapshot recording its backend node and volume group.
LOCATION_LABEL = "lvm.driver.harvesterhci.io/snapshot-location"
HOST_POD_IMAGE = os.getenv("WORKLOAD_POD_IMAGE", "busybox:1.36.1")


class lvm_driver_keywords:
    """Layer 3: LVM driver internals verification"""

    def __init__(self):
        init_k8s_api_client()
        self.core_api = client.CoreV1Api()
        self.obj_api = client.CustomObjectsApi()

    # ---- snapshot handle plumbing ----

    def get_snapshot_handle(self, snapshot_name, namespace=DEFAULT_NAMESPACE):
        """Resolve a VolumeSnapshot to its CSI snapshot handle."""
        snapshot = self.obj_api.get_namespaced_custom_object(
            group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
            namespace=namespace, plural="volumesnapshots",
            name=snapshot_name)
        content_name = snapshot.get("status", {}).get(
            "boundVolumeSnapshotContentName")
        assert content_name, (
            f"VolumeSnapshot {snapshot_name} has no bound content yet")
        content = self.obj_api.get_cluster_custom_object(
            group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
            plural="volumesnapshotcontents", name=content_name)
        handle = content.get("status", {}).get("snapshotHandle")
        assert handle, (
            f"VolumeSnapshotContent {content_name} has no snapshotHandle yet")
        return handle

    # ---- location records (harvester/csi-driver-lvm#64) ----

    def get_snapshot_location_record(self, snapshot_handle):
        """Return {node, vg} recorded for the handle, or None when absent."""
        config_maps = self.core_api.list_namespaced_config_map(
            namespace=LVM_DRIVER_NAMESPACE,
            label_selector=f"{LOCATION_LABEL}=true")
        for config_map in config_maps.items:
            data = config_map.data or {}
            if data.get("snapshotHandle") == snapshot_handle:
                return {"node": data.get("nodeName"),
                        "vg": data.get("vgName")}
        return None

    def location_record_should_exist(self, snapshot_handle, node, vg):
        record = self.get_snapshot_location_record(snapshot_handle)
        assert record is not None, (
            f"No location record found for snapshot handle {snapshot_handle}")
        assert record["node"] == node and record["vg"] == vg, (
            f"Location record mismatch for {snapshot_handle}: "
            f"recorded {record}, expected node={node} vg={vg}")

    def location_record_should_not_exist(self, snapshot_handle):
        retry_count, retry_interval = get_retry_count_and_interval()
        for _ in range(retry_count):
            if self.get_snapshot_location_record(snapshot_handle) is None:
                return
            time.sleep(retry_interval)
        raise AssertionError(
            f"Location record for {snapshot_handle} was not removed in time")

    # ---- backend LV verification on the node ----

    def _host_exec(self, node_name, command):
        """Run a command in the host namespaces of node_name via a transient
        privileged hostPID pod (nsenter into PID 1), and return stdout."""
        pod_name = f"lvm-host-probe-{int(time.time() * 1000) % 1000000}"
        body = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name,
                "namespace": DEFAULT_NAMESPACE,
                "labels": {"app": "harvester-e2e-host-probe"},
            },
            "spec": {
                "nodeName": node_name,
                "restartPolicy": "Never",
                "hostPID": True,
                "terminationGracePeriodSeconds": 0,
                "tolerations": [{"operator": "Exists"}],
                "containers": [{
                    "name": "probe",
                    "image": HOST_POD_IMAGE,
                    "command": ["sh", "-c", "sleep 300"],
                    "securityContext": {"privileged": True,
                                        "runAsUser": 0},
                }],
            },
        }
        self.core_api.create_namespaced_pod(
            namespace=DEFAULT_NAMESPACE, body=body)
        try:
            retry_count, retry_interval = get_retry_count_and_interval()
            for _ in range(retry_count):
                pod = self.core_api.read_namespaced_pod(
                    name=pod_name, namespace=DEFAULT_NAMESPACE)
                if pod.status and pod.status.phase == "Running":
                    break
                time.sleep(retry_interval)
            else:
                raise AssertionError(
                    f"Host probe pod on {node_name} did not start")
            resp = stream(
                self.core_api.connect_get_namespaced_pod_exec,
                pod_name, DEFAULT_NAMESPACE,
                command=["nsenter", "-t", "1", "-m", "-u", "-i", "-n",
                         "--", "sh", "-c", command],
                stderr=True, stdin=False, stdout=True, tty=False,
                _preload_content=False)
            stdout = []
            while resp.is_open():
                resp.update(timeout=5)
                if resp.peek_stdout():
                    stdout.append(resp.read_stdout())
                if resp.peek_stderr():
                    resp.read_stderr()
            resp.close()
            return "".join(stdout).strip()
        finally:
            try:
                self.core_api.delete_namespaced_pod(
                    name=pod_name, namespace=DEFAULT_NAMESPACE,
                    grace_period_seconds=0)
            except ApiException:
                pass

    def lv_exists_on_node(self, node_name, vg_name, lv_name):
        """Check via the host's lvm tools whether vg/lv exists."""
        out = self._host_exec(
            node_name,
            f"lvs --noheadings -o lv_name {vg_name} 2>/dev/null || true")
        names = [line.strip() for line in out.splitlines()]
        exists = lv_name in names
        logging(f"LV {vg_name}/{lv_name} on {node_name}: "
                f"{'present' if exists else 'absent'}")
        return exists

    def snapshot_lv_should_exist(self, node_name, vg_name, snapshot_handle):
        assert self.lv_exists_on_node(
            node_name, vg_name, f"lvm-{snapshot_handle}"), (
            f"Backend LV lvm-{snapshot_handle} not found in {vg_name} "
            f"on {node_name}")

    def snapshot_lv_should_not_exist(self, node_name, vg_name,
                                     snapshot_handle):
        retry_count, retry_interval = get_retry_count_and_interval()
        for _ in range(retry_count):
            if not self.lv_exists_on_node(
                    node_name, vg_name, f"lvm-{snapshot_handle}"):
                return
            time.sleep(retry_interval)
        raise AssertionError(
            f"Backend LV lvm-{snapshot_handle} still present in {vg_name} "
            f"on {node_name}")

    def no_pv_should_reference_claim(self, pvc_name,
                                     namespace=DEFAULT_NAMESPACE):
        """Assert no PersistentVolume (e.g. stuck in Released) still
        references the claim; retries to allow reclaim to finish."""
        retry_count, retry_interval = get_retry_count_and_interval()
        leftover = None
        for _ in range(retry_count):
            leftover = None
            for pv in self.core_api.list_persistent_volume().items:
                ref = pv.spec.claim_ref
                if ref and ref.name == pvc_name and ref.namespace == namespace:
                    leftover = f"{pv.metadata.name} (phase {pv.status.phase})"
                    break
            if leftover is None:
                return
            time.sleep(retry_interval)
        raise AssertionError(
            f"PV {leftover} still references deleted claim {pvc_name}")

    # ---- retain-policy and pre-provisioned snapshot flow ----

    def create_retain_snapshot_class(self, class_name):
        body = {
            "apiVersion": f"{SNAPSHOT_GROUP}/{SNAPSHOT_VERSION}",
            "kind": "VolumeSnapshotClass",
            "metadata": {"name": class_name},
            "driver": LVM_DRIVER_NAME,
            "deletionPolicy": "Retain",
        }
        try:
            self.obj_api.create_cluster_custom_object(
                group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
                plural="volumesnapshotclasses", body=body)
        except ApiException as e:
            if e.status != 409:
                raise

    def delete_snapshot_class(self, class_name):
        try:
            self.obj_api.delete_cluster_custom_object(
                group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
                plural="volumesnapshotclasses", name=class_name)
        except ApiException as e:
            if e.status != 404:
                raise

    def release_snapshot_keeping_backend(self, snapshot_name,
                                         namespace=DEFAULT_NAMESPACE):
        """Delete a Retain-policy VolumeSnapshot and its content objects
        without touching the backend LV, and return the orphaned handle."""
        handle = self.get_snapshot_handle(snapshot_name, namespace)
        snapshot = self.obj_api.get_namespaced_custom_object(
            group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
            namespace=namespace, plural="volumesnapshots",
            name=snapshot_name)
        content_name = snapshot["status"]["boundVolumeSnapshotContentName"]
        self.obj_api.delete_namespaced_custom_object(
            group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
            namespace=namespace, plural="volumesnapshots",
            name=snapshot_name)
        self._wait_for_content_released(content_name)
        self.obj_api.delete_cluster_custom_object(
            group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
            plural="volumesnapshotcontents", name=content_name)
        return handle

    def _wait_for_content_released(self, content_name):
        retry_count, retry_interval = get_retry_count_and_interval()
        for _ in range(retry_count):
            try:
                content = self.obj_api.get_cluster_custom_object(
                    group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
                    plural="volumesnapshotcontents", name=content_name)
            except ApiException as e:
                if e.status == 404:
                    return
                raise
            if not content.get("spec", {}).get("volumeSnapshotRef", {}) \
                    .get("uid"):
                return
            time.sleep(retry_interval)

    def import_preprovisioned_snapshot(self, snapshot_name, snapshot_handle,
                                       size, namespace=DEFAULT_NAMESPACE):
        """Re-import an orphaned backend snapshot as a pre-provisioned
        VolumeSnapshotContent + VolumeSnapshot pair.

        Deliberately sets no node/vg annotations on the content: resolving
        the backend location must work through the driver's location
        records (harvester/csi-driver-lvm#64).
        """
        content_name = f"{snapshot_name}-content"
        content = {
            "apiVersion": f"{SNAPSHOT_GROUP}/{SNAPSHOT_VERSION}",
            "kind": "VolumeSnapshotContent",
            "metadata": {"name": content_name},
            "spec": {
                "deletionPolicy": "Delete",
                "driver": LVM_DRIVER_NAME,
                "source": {"snapshotHandle": snapshot_handle},
                "volumeSnapshotRef": {
                    "name": snapshot_name,
                    "namespace": namespace,
                },
            },
        }
        snapshot = {
            "apiVersion": f"{SNAPSHOT_GROUP}/{SNAPSHOT_VERSION}",
            "kind": "VolumeSnapshot",
            "metadata": {"name": snapshot_name, "namespace": namespace},
            "spec": {
                "source": {"volumeSnapshotContentName": content_name},
            },
        }
        self.obj_api.create_cluster_custom_object(
            group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
            plural="volumesnapshotcontents", body=content)
        self.obj_api.create_namespaced_custom_object(
            group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
            namespace=namespace, plural="volumesnapshots", body=snapshot)

    def delete_imported_snapshot(self, snapshot_name,
                                 namespace=DEFAULT_NAMESPACE):
        """Delete a pre-provisioned VolumeSnapshot and wait until its content
        is gone, which requires the driver to delete the backend LV."""
        try:
            self.obj_api.delete_namespaced_custom_object(
                group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
                namespace=namespace, plural="volumesnapshots",
                name=snapshot_name)
        except ApiException as e:
            if e.status != 404:
                raise
        content_name = f"{snapshot_name}-content"
        retry_count, retry_interval = get_retry_count_and_interval()
        for _ in range(retry_count):
            try:
                self.obj_api.get_cluster_custom_object(
                    group=SNAPSHOT_GROUP, version=SNAPSHOT_VERSION,
                    plural="volumesnapshotcontents", name=content_name)
            except ApiException as e:
                if e.status == 404:
                    return
                raise
            time.sleep(retry_interval)
        raise AssertionError(
            f"VolumeSnapshotContent {content_name} was not removed in time; "
            "the driver likely failed to delete the backend snapshot")
