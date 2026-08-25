"""
Pod component - delegates to CRD or REST implementation.
"""
import os

from constant import HarvesterOperationStrategy, DEFAULT_TIMEOUT_SHORT
from pod.crd import CRD
from pod.rest import Rest


class Pod:
    """Pod component - selects implementation by HARVESTER_OPERATION_STRATEGY."""

    def __init__(self):
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        if strategy_str == HarvesterOperationStrategy.REST.value:
            self.pod = Rest()
        else:
            self.pod = CRD()

    def create(self, pod_name, namespace, spec):
        return self.pod.create(pod_name, namespace, spec)

    def delete_if_exists(self, pod_name, namespace):
        return self.pod.delete_if_exists(pod_name, namespace)

    def wait_for_succeeded(self, pod_name, namespace, timeout=DEFAULT_TIMEOUT_SHORT):
        return self.pod.wait_for_succeeded(pod_name, namespace, timeout)

    def get_logs(self, pod_name, namespace):
        return self.pod.get_logs(pod_name, namespace)
