"""
Pod REST Implementation stub.
Pods are native Kubernetes resources with no Harvester REST API endpoint;
all operations must use the CRD (CoreV1Api) strategy.
"""
from pod.base import Base


class Rest(Base):
    """Pod REST stub - not implemented; use HARVESTER_OPERATION_STRATEGY=crd."""

    def _not_implemented(self, method):
        raise NotImplementedError(
            f"Pod.{method} is only implemented for the CRD strategy; "
            "run with HARVESTER_OPERATION_STRATEGY=crd"
        )

    def create(self, pod_name, namespace, spec):
        self._not_implemented("create")

    def delete_if_exists(self, pod_name, namespace):
        self._not_implemented("delete_if_exists")

    def wait_for_succeeded(self, pod_name, namespace, timeout):
        self._not_implemented("wait_for_succeeded")

    def get_logs(self, pod_name, namespace):
        self._not_implemented("get_logs")
