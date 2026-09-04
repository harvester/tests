
"""
Layer 3: Workload Keywords - plain pods consuming PVCs for data-integrity
checks. Talks to the Kubernetes API directly; there is no Harvester REST
equivalent for these operations, so no CRD/REST strategy split.
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

WORKLOAD_POD_IMAGE = os.getenv("WORKLOAD_POD_IMAGE", "busybox:1.36.1")
BLOCK_DEVICE_PATH = "/dev/test-volume"
FILESYSTEM_MOUNT_PATH = "/data"
LABEL_WORKLOAD = "harvester-e2e-workload"


class workload_keywords:
    """Layer 3: Workload keyword wrapper - pod lifecycle and in-pod IO"""

    def __init__(self):
        init_k8s_api_client()
        self.core_api = client.CoreV1Api()

    def _pod_manifest(self, pod_name, pvc_name, volume_mode):
        volume = {
            "name": "test-volume",
            "persistentVolumeClaim": {"claimName": pvc_name},
        }
        container = {
            "name": "workload",
            "image": WORKLOAD_POD_IMAGE,
            "command": ["sh", "-c", "sleep infinity"],
            "securityContext": {"runAsUser": 0},
        }
        if volume_mode == "Block":
            container["volumeDevices"] = [
                {"name": "test-volume", "devicePath": BLOCK_DEVICE_PATH}
            ]
        else:
            container["volumeMounts"] = [
                {"name": "test-volume", "mountPath": FILESYSTEM_MOUNT_PATH}
            ]
        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name,
                "namespace": DEFAULT_NAMESPACE,
                "labels": {"app": LABEL_WORKLOAD},
            },
            "spec": {
                "restartPolicy": "Never",
                "terminationGracePeriodSeconds": 0,
                "containers": [container],
                "volumes": [volume],
            },
        }

    def create_workload_pod(self, pod_name, pvc_name, volume_mode="Block",
                            wait=True):
        """Create a pod consuming the PVC and wait until it is Running.

        volume_mode must match the PVC's volumeMode: Block exposes the volume
        at /dev/test-volume, Filesystem mounts it at /data. Pass wait=False
        when the pod only has to exist to trigger provisioning and is never
        expected to run (negative tests).
        """
        logging(f'Creating workload pod {pod_name} for PVC {pvc_name} '
                f'({volume_mode})')
        body = self._pod_manifest(pod_name, pvc_name, volume_mode)
        try:
            self.core_api.create_namespaced_pod(
                namespace=DEFAULT_NAMESPACE, body=body)
        except ApiException as e:
            raise AssertionError(
                f"Failed to create workload pod {pod_name}: {e}")
        if wait:
            self._wait_for_pod_running(pod_name)

    def _wait_for_pod_running(self, pod_name):
        retry_count, retry_interval = get_retry_count_and_interval()
        pod = None
        for _ in range(retry_count):
            try:
                pod = self.core_api.read_namespaced_pod(
                    name=pod_name, namespace=DEFAULT_NAMESPACE)
                if pod.status and pod.status.phase == "Running":
                    return
            except ApiException as e:
                logging(f"Reading pod {pod_name} failed: {e}", level="DEBUG")
            time.sleep(retry_interval)
        raise AssertionError(
            f"Workload pod {pod_name} did not reach Running in time; "
            f"{self._pod_diagnostics(pod_name, pod)}")

    def _pod_diagnostics(self, pod_name, pod):
        """Summarize pod phase, container states, its PVC phase, and recent
        events so a startup timeout is diagnosable after teardown."""
        parts = []
        try:
            if pod is not None and pod.status:
                parts.append(f"phase={pod.status.phase}")
                for cs in (pod.status.container_statuses or []):
                    if cs.state and cs.state.waiting:
                        parts.append(
                            f"container waiting: {cs.state.waiting.reason} "
                            f"{cs.state.waiting.message or ''}".strip())
            if pod is not None:
                for volume in (pod.spec.volumes or []):
                    if not volume.persistent_volume_claim:
                        continue
                    claim = volume.persistent_volume_claim.claim_name
                    pvc = self.core_api.read_namespaced_persistent_volume_claim(
                        name=claim, namespace=DEFAULT_NAMESPACE)
                    parts.append(f"pvc {claim} phase={pvc.status.phase}")
                    events = self.core_api.list_namespaced_event(
                        namespace=DEFAULT_NAMESPACE,
                        field_selector=f"involvedObject.name={claim}")
                    for event in events.items[-3:]:
                        parts.append(f"pvc event: {event.reason}: "
                                     f"{(event.message or '')[:200]}")
            events = self.core_api.list_namespaced_event(
                namespace=DEFAULT_NAMESPACE,
                field_selector=f"involvedObject.name={pod_name}")
            for event in events.items[-3:]:
                parts.append(f"pod event: {event.reason}: "
                             f"{(event.message or '')[:200]}")
        except ApiException as e:
            parts.append(f"(diagnostics collection failed: {e.status})")
        return "; ".join(parts) if parts else "(no diagnostics available)"

    def delete_workload_pod(self, pod_name):
        """Delete the pod and wait until it is gone, so the volume is
        unpublished before the next consumer attaches it."""
        logging(f'Deleting workload pod {pod_name}')
        try:
            self.core_api.delete_namespaced_pod(
                name=pod_name, namespace=DEFAULT_NAMESPACE,
                grace_period_seconds=0)
        except ApiException as e:
            if e.status == 404:
                return
            raise AssertionError(
                f"Failed to delete workload pod {pod_name}: {e}")
        retry_count, retry_interval = get_retry_count_and_interval()
        for _ in range(retry_count):
            try:
                self.core_api.read_namespaced_pod(
                    name=pod_name, namespace=DEFAULT_NAMESPACE)
            except ApiException as e:
                if e.status == 404:
                    return
            time.sleep(retry_interval)
        raise AssertionError(f"Workload pod {pod_name} was not removed in time")

    def _exec(self, pod_name, command):
        """Run a shell command in the pod and return stdout.

        Raises AssertionError when the command exits non-zero, with the
        combined output in the message.
        """
        logging(f'Executing in pod {pod_name}: {command}', level="DEBUG")
        resp = stream(
            self.core_api.connect_get_namespaced_pod_exec,
            pod_name,
            DEFAULT_NAMESPACE,
            command=["sh", "-c", command],
            stderr=True, stdin=False, stdout=True, tty=False,
            _preload_content=False,
        )
        stdout, stderr = [], []
        while resp.is_open():
            resp.update(timeout=5)
            if resp.peek_stdout():
                stdout.append(resp.read_stdout())
            if resp.peek_stderr():
                stderr.append(resp.read_stderr())
        resp.close()
        rc = resp.returncode
        if rc != 0:
            raise AssertionError(
                f"Command failed in pod {pod_name} (rc={rc}): {command}\n"
                f"stdout: {''.join(stdout)}\nstderr: {''.join(stderr)}")
        return "".join(stdout).strip()

    def write_block_pattern(self, pod_name, size_mb=128):
        """Write a deterministic pattern over the head of the block volume
        and return its checksum.

        The pattern is random data with an explicit all-zero region in the
        middle (1/4 to 3/4 of the range). The zero region is intentional: it
        verifies that snapshot/clone paths preserve zeros instead of leaving
        stale disk content behind (sparse-copy optimizations must not skip
        regions the source really contains as zeros).
        """
        size_mb = int(size_mb)
        quarter = size_mb // 4
        dev = BLOCK_DEVICE_PATH
        tail = size_mb - 3 * quarter
        self._exec(pod_name, (
            f"dd if=/dev/urandom of={dev} bs=1M count={quarter} 2>/dev/null && "
            f"dd if=/dev/zero of={dev} bs=1M seek={quarter} "
            f"count={2 * quarter} 2>/dev/null && "
            f"dd if=/dev/urandom of={dev} bs=1M seek={3 * quarter} "
            f"count={tail} 2>/dev/null && "
            "sync"
        ))
        return self.block_checksum(pod_name, size_mb)

    def overwrite_block_head(self, pod_name, size_mb=8):
        """Scribble over the start of the block volume, so a later checksum
        proves a restored volume is independent from the source."""
        self._exec(pod_name, (
            f"dd if=/dev/urandom of={BLOCK_DEVICE_PATH} bs=1M "
            f"count={int(size_mb)} 2>/dev/null && sync"
        ))

    def block_checksum(self, pod_name, size_mb=128):
        """Checksum the first size_mb MiB of the block volume."""
        out = self._exec(pod_name, (
            f"dd if={BLOCK_DEVICE_PATH} bs=1M count={int(size_mb)} "
            "2>/dev/null | sha256sum"
        ))
        return out.split()[0]

    def write_filesystem_file(self, pod_name, size_mb=16):
        """Write a random file on the mounted filesystem and return its
        checksum."""
        path = f"{FILESYSTEM_MOUNT_PATH}/data.bin"
        self._exec(pod_name, (
            f"dd if=/dev/urandom of={path} bs=1M count={int(size_mb)} "
            "2>/dev/null && sync"
        ))
        out = self._exec(pod_name, f"sha256sum {path}")
        return out.split()[0]

    def filesystem_file_checksum(self, pod_name):
        """Checksum the data file; fails when the file is missing, which is
        exactly what a re-format would cause."""
        out = self._exec(pod_name, f"sha256sum {FILESYSTEM_MOUNT_PATH}/data.bin")
        return out.split()[0]

    def filesystem_capacity_mb(self, pod_name):
        """Return the mounted filesystem's total size in MiB (df -m), so
        tests can verify an expansion actually resized the filesystem."""
        out = self._exec(pod_name, (
            f"df -Pm {FILESYSTEM_MOUNT_PATH} | awk 'NR==2 {{print $2}}'"
        ))
        return int(out)
