"""
Pod Keywords for Robot Framework
Wraps generic pod lifecycle operations.
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))  # noqa: E402

from kubernetes import client  # noqa: E402
from kubernetes.client.rest import ApiException  # noqa: E402
from utility.utility import logging, get_retry_count_and_interval  # noqa: E402


class pod_keywords:
    """Robot Framework keyword library for generic pod lifecycle operations."""

    def __init__(self):
        self._core_api = None
        self.retry_count, self.retry_interval = get_retry_count_and_interval()

    @property
    def core_api(self):
        if self._core_api is None:
            self._core_api = client.CoreV1Api()
        return self._core_api

    def create_pod(self, pod_name, namespace, spec):
        """Create a pod from a spec dict (idempotent — deletes any existing pod first)."""
        self.delete_pod_if_exists(pod_name, namespace)
        body = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": pod_name, "namespace": namespace},
            "spec": spec,
        }
        self.core_api.create_namespaced_pod(namespace=namespace, body=body)
        logging(f"Created pod '{pod_name}' in namespace '{namespace}'")

    def wait_for_pod_succeeded(self, pod_name, namespace, timeout=300):
        """Wait until the pod reaches the Succeeded phase."""
        timeout = int(timeout)
        endtime = time.time() + timeout

        while time.time() < endtime:
            try:
                pod = self.core_api.read_namespaced_pod(name=pod_name, namespace=namespace)
                phase = pod.status.phase

                if phase == "Succeeded":
                    logging(f"Pod '{pod_name}' succeeded")
                    return True
                if phase == "Failed":
                    raise AssertionError(f"Pod '{pod_name}' entered Failed phase")

                logging(f"Pod '{pod_name}' phase={phase}, waiting…")
            except ApiException as e:
                logging(f"Error polling pod '{pod_name}': {e}", level="WARNING")

            time.sleep(self.retry_interval)

        raise AssertionError(f"Pod '{pod_name}' did not reach Succeeded within {timeout}s")

    def get_pod_logs(self, pod_name, namespace):
        """Return the full log output of a pod as a string."""
        logs = self.core_api.read_namespaced_pod_log(name=pod_name, namespace=namespace)
        logging(f"Logs for pod '{pod_name}':\n{logs}")
        return logs

    def delete_pod_if_exists(self, pod_name, namespace):
        """Delete a pod if it exists; silently ignores 404."""
        try:
            self.core_api.delete_namespaced_pod(
                name=pod_name,
                namespace=namespace,
                body=client.V1DeleteOptions(grace_period_seconds=0),
            )
            logging(f"Deleted pod '{pod_name}' from namespace '{namespace}'")
            time.sleep(3)
        except ApiException as e:
            if e.status != 404:
                logging(f"Error deleting pod '{pod_name}': {e}", level="WARNING")
