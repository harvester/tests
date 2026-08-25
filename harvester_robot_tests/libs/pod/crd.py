"""
Pod CRD Implementation - uses Kubernetes CoreV1Api.
"""
import time

from kubernetes import client
from kubernetes.client.rest import ApiException

from pod.base import Base
from utility.utility import logging, get_retry_count_and_interval


class CRD(Base):
    """Pod implementation backed by the Kubernetes CoreV1Api."""

    def __init__(self):
        self._core_api = None
        self.retry_count, self.retry_interval = get_retry_count_and_interval()

    @property
    def core_api(self):
        if self._core_api is None:
            self._core_api = client.CoreV1Api()
        return self._core_api

    def create(self, pod_name, namespace, spec):
        """Create a pod from a spec dict (idempotent — deletes any existing pod first)."""
        self.delete_if_exists(pod_name, namespace)
        body = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": pod_name, "namespace": namespace},
            "spec": spec,
        }
        self.core_api.create_namespaced_pod(namespace=namespace, body=body)
        logging(f"Created pod '{pod_name}' in namespace '{namespace}'")

    def delete_if_exists(self, pod_name, namespace):
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

    def wait_for_succeeded(self, pod_name, namespace, timeout):
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

                logging(f"Pod '{pod_name}' phase={phase}, waiting...")
            except ApiException as e:
                logging(f"Error polling pod '{pod_name}': {e}", level="WARNING")

            time.sleep(self.retry_interval)

        raise AssertionError(f"Pod '{pod_name}' did not reach Succeeded within {timeout}s")

    def get_logs(self, pod_name, namespace):
        """Return the full log output of a pod as a string."""
        logs = self.core_api.read_namespaced_pod_log(name=pod_name, namespace=namespace)
        logging(f"Logs for pod '{pod_name}':\n{logs}")
        return logs
