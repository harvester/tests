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

    def wait_for_running_with_label_selector(self, namespace, label_selector, timeout):
        """
        Wait for pods to be running in a namespace

        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector to filter pods
            timeout: Timeout in seconds
        """
        logging(
            f"Waiting for pods with selector '{label_selector}' in namespace "
            f"'{namespace}' to be running"
        )
        max_retries = int(timeout / self.retry_interval)

        for i in range(max_retries):
            try:
                pods = self.core_api.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector
                )

                if len(pods.items) == 0:
                    logging(
                        f"No pods found with selector '{label_selector}', retrying... "
                        f"({i+1}/{max_retries})"
                    )
                    time.sleep(self.retry_interval)
                    continue

                all_running = True
                for pod in pods.items:
                    if pod.status.phase != 'Running':
                        all_running = False
                        break

                    # Check if all containers are ready
                    if pod.status.container_statuses:
                        for container_status in pod.status.container_statuses:
                            if not container_status.ready:
                                all_running = False
                                break

                if all_running:
                    logging(f"All pods with selector '{label_selector}' are running")
                    return True

                logging(
                    f"Pods not yet all running, retrying... "
                    f"({i+1}/{max_retries})"
                )
                time.sleep(self.retry_interval)

            except ApiException as e:
                logging(f"Error listing pods: {e}", level='WARNING')
                time.sleep(self.retry_interval)

        raise TimeoutError(
            f"Timeout waiting for pods with selector '{label_selector}' "
            f"to be running after {timeout}s"
        )

    def wait_for_gone_with_label_selector(self, namespace, label_selector, timeout):
        """
        Wait until no pods matching the label selector remain in the namespace

        Used after disabling an addon to confirm its workload was torn down.

        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector to filter pods
            timeout: Timeout in seconds
        """
        logging(
            f"Waiting for pods with selector '{label_selector}' in namespace "
            f"'{namespace}' to be gone"
        )
        max_retries = int(timeout / self.retry_interval)

        for i in range(max_retries):
            try:
                pods = self.core_api.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector
                )

                if len(pods.items) == 0:
                    logging(f"No pods with selector '{label_selector}' remain")
                    return True

                logging(
                    f"{len(pods.items)} pod(s) with selector '{label_selector}' still "
                    f"present, retrying... ({i+1}/{max_retries})"
                )
            except ApiException as e:
                logging(f"Error listing pods: {e}", level='WARNING')

            time.sleep(self.retry_interval)

        raise TimeoutError(
            f"Timeout waiting for pods with selector '{label_selector}' "
            f"to be gone after {timeout}s"
        )

    def get_logs(self, pod_name, namespace):
        """Return the full log output of a pod as a string."""
        logs = self.core_api.read_namespaced_pod_log(name=pod_name, namespace=namespace)
        logging(f"Logs for pod '{pod_name}':\n{logs}")
        return logs
