"""
HelmChart CRD Implementation
Layer 4: Kubernetes API operations for helm.cattle.io HelmChart resources.
"""
import time

from kubernetes import client
from kubernetes.client.rest import ApiException
from utility.utility import logging, get_retry_count_and_interval
from constant import DEFAULT_TIMEOUT_LONG

HELMCHART_GROUP = "helm.cattle.io"
HELMCHART_VERSION = "v1"
HELMCHART_PLURAL = "helmcharts"


class CRD:
    """Kubernetes API operations for HelmChart CRs."""

    def __init__(self):
        self.custom_api = client.CustomObjectsApi()
        self.batch_api = client.BatchV1Api()
        self.retry_count, self.retry_interval = get_retry_count_and_interval()

    def _wait_for_gone(self, name, namespace, endtime):
        """Poll until the HelmChart CR is absent or endtime is reached."""
        while time.time() < endtime:
            try:
                self.custom_api.get_namespaced_custom_object(
                    group=HELMCHART_GROUP, version=HELMCHART_VERSION,
                    namespace=namespace, plural=HELMCHART_PLURAL, name=name,
                )
                time.sleep(self.retry_interval)
            except ApiException as e:
                if e.status == 404:
                    return
                raise
        raise AssertionError(
            f"HelmChart '{name}' was not removed within the allotted time"
        )

    def create(self, name, namespace, spec):
        """
        Create a HelmChart CR with the given spec.

        Deletes any pre-existing CR first so the call is idempotent.
        """
        try:
            self.custom_api.delete_namespaced_custom_object(
                group=HELMCHART_GROUP, version=HELMCHART_VERSION,
                namespace=namespace, plural=HELMCHART_PLURAL, name=name,
            )
            logging(f"Deleted pre-existing HelmChart '{name}'; waiting for finalizer to clear…")
            self._wait_for_gone(name, namespace, time.time() + int(DEFAULT_TIMEOUT_LONG))
        except ApiException as e:
            if e.status != 404:
                logging(f"Error deleting existing HelmChart: {e}", level="WARNING")

        body = {
            "apiVersion": f"{HELMCHART_GROUP}/{HELMCHART_VERSION}",
            "kind": "HelmChart",
            "metadata": {"name": name, "namespace": namespace},
            "spec": spec,
        }
        self.custom_api.create_namespaced_custom_object(
            group=HELMCHART_GROUP, version=HELMCHART_VERSION,
            namespace=namespace, plural=HELMCHART_PLURAL, body=body,
        )
        logging(f"Created HelmChart '{name}' in namespace '{namespace}'")

    def wait_for_deployed(self, name, namespace, timeout=DEFAULT_TIMEOUT_LONG):
        """
        Wait until the HelmChart install Job completes successfully.

        Phase 1 — poll until the controller sets status.jobName.
        Phase 2 — poll the Job until it has a Complete condition.
        """
        timeout = int(timeout)
        endtime = time.time() + timeout
        job_name = None

        while time.time() < endtime:
            try:
                hc = self.custom_api.get_namespaced_custom_object(
                    group=HELMCHART_GROUP, version=HELMCHART_VERSION,
                    namespace=namespace, plural=HELMCHART_PLURAL, name=name,
                )
                job_name = hc.get("status", {}).get("jobName")
                if job_name:
                    logging(f"HelmChart '{name}' install job: {job_name}")
                    break
            except ApiException as e:
                logging(f"Error polling HelmChart '{name}': {e}", level="WARNING")
            logging(f"Waiting for HelmChart '{name}' job to be created…")
            time.sleep(self.retry_interval)
        else:
            raise AssertionError(
                f"HelmChart '{name}' did not get an install job within {timeout}s"
            )

        while time.time() < endtime:
            try:
                job = self.batch_api.read_namespaced_job(name=job_name, namespace=namespace)
                for condition in (job.status.conditions or []):
                    if condition.type == "Complete" and condition.status == "True":
                        logging(f"HelmChart install job '{job_name}' completed")
                        return True
                    if condition.type == "Failed" and condition.status == "True":
                        raise AssertionError(f"HelmChart install job '{job_name}' failed")
            except ApiException as e:
                logging(f"Error polling job '{job_name}': {e}", level="WARNING")
            logging(f"Waiting for HelmChart job '{job_name}' to complete…")
            time.sleep(self.retry_interval)

        raise AssertionError(f"HelmChart job '{job_name}' did not complete within {timeout}s")

    def delete(self, name, namespace, timeout=DEFAULT_TIMEOUT_LONG):
        """Delete a HelmChart CR and wait until the finalizer is cleared."""
        try:
            logging(f"Deleting HelmChart '{name}' from namespace '{namespace}'")
            self.custom_api.delete_namespaced_custom_object(
                group=HELMCHART_GROUP, version=HELMCHART_VERSION,
                namespace=namespace, plural=HELMCHART_PLURAL, name=name,
            )
            logging(f"Deleted HelmChart '{name}' from namespace '{namespace}'")
        except ApiException as e:
            if e.status == 404:
                logging(f"HelmChart '{name}' already absent")
                return
            logging(f"Error deleting HelmChart '{name}': {e}", level="WARNING")
            raise

        self._wait_for_gone(name, namespace, time.time() + int(timeout))
        logging(f"HelmChart '{name}' fully removed")
