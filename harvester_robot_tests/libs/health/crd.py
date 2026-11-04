"""
Health CRD Implementation - Kubernetes API operations
Layer 4: reads the cluster-scoped ComponentHealth resources that back the
Resource Health Dashboard (https://github.com/harvester/harvester/issues/8436).
"""
import time

from kubernetes.client.rest import ApiException

from constant import (
    DEFAULT_TIMEOUT,
    HEALTH_API_GROUP,
    HEALTH_API_VERSION,
    COMPONENT_HEALTH_PLURAL,
)
from crd import get_cluster_cr
from health.base import Base
from utility.utility import logging, get_retry_count_and_interval


class CRD(Base):
    """CRD implementation for Health operations using Kubernetes API"""

    def __init__(self):
        self.retry_count, self.retry_interval = get_retry_count_and_interval()

    def _get_component_health(self, name):
        return get_cluster_cr(
            HEALTH_API_GROUP, HEALTH_API_VERSION, COMPONENT_HEALTH_PLURAL, name)

    def component_health_exists(self, name):
        try:
            self._get_component_health(name)
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            raise

    def get_check(self, component_health_name, check_name):
        component_health = self._get_component_health(component_health_name)
        checks = component_health.get("status", {}).get("checks") or {}
        return checks.get(check_name)

    def wait_for_check_affects_resource(self, component_health_name, check_name,
                                        resource_name, timeout=DEFAULT_TIMEOUT):
        logging(f"Waiting for {component_health_name} check {check_name} "
                f"to report {resource_name} (timeout: {timeout}s)")
        max_retries = max(int(int(timeout) / self.retry_interval), 1)
        check = None
        for _ in range(max_retries):
            check = self.get_check(component_health_name, check_name)
            affected = ((check or {}).get("affectedResources") or {}).get("names") or {}
            if resource_name in affected:
                logging(f"Check {check_name} reports {resource_name}: {check}")
                return check
            time.sleep(self.retry_interval)

        raise AssertionError(
            f"{component_health_name} check {check_name} did not report {resource_name} "
            f"within {timeout}s, last seen: {check}")
