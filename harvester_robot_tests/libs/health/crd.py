"""
Health CRD Implementation - Kubernetes API operations
Layer 4: reads the cluster-scoped ComponentHealth resources that back the
Resource Health Dashboard (https://github.com/harvester/harvester/issues/8436).
"""
import time
from datetime import datetime, timedelta, timezone

from kubernetes.client.rest import ApiException

from constant import (
    DEFAULT_TIMEOUT,
    HEALTH_API_GROUP,
    HEALTH_API_VERSION,
    COMPONENT_HEALTH_PLURAL,
    HEALTH_IGNORE_RULE_KIND,
    HEALTH_IGNORE_RULE_PLURAL,
    HEALTH_IGNORE_RULE_SOURCE_LABEL,
)
from crd import get_cluster_cr, create_cluster_cr, patch_cluster_cr, delete_cluster_cr
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

    def _wait_for(self, description, predicate, timeout):
        """Poll predicate() until it returns a truthy value and return that value."""
        logging(f"Waiting for {description} (timeout: {timeout}s)")
        max_retries = max(int(int(timeout) / self.retry_interval), 1)
        for _ in range(max_retries):
            result = predicate()
            if result:
                return result
            time.sleep(self.retry_interval)
        raise AssertionError(f"Timed out after {timeout}s waiting for {description}")

    def wait_for_resource_ignored_state(self, component_health_name, check_name,
                                        resource_name, ignored, timeout=DEFAULT_TIMEOUT):
        ignored = str(ignored).lower() == "true"

        def predicate():
            check = self.get_check(component_health_name, check_name) or {}
            names = (check.get("affectedResources") or {}).get("names") or {}
            if resource_name not in names:
                return None
            return check if bool((names[resource_name] or {}).get("ignored")) == ignored \
                else None

        return self._wait_for(
            f"{component_health_name} check {check_name} to mark {resource_name} "
            f"ignored={ignored}", predicate, timeout)

    def wait_for_check_ignored_state(self, component_health_name, check_name,
                                     ignored, timeout=DEFAULT_TIMEOUT):
        ignored = str(ignored).lower() == "true"

        def predicate():
            check = self.get_check(component_health_name, check_name)
            if check is None:
                return None
            return check if bool(check.get("ignored")) == ignored else None

        return self._wait_for(
            f"{component_health_name} check {check_name} to be ignored={ignored}",
            predicate, timeout)

    def create_ignore_rule(self, name, component_health_name, check_name,
                           resources=None, expires_at=None, reason=None):
        spec = {"componentHealth": component_health_name, "checkKey": check_name}
        if resources:
            spec["resources"] = list(resources)
        if expires_at:
            spec["expiresAt"] = expires_at
        if reason:
            spec["reason"] = reason
        body = {
            "apiVersion": f"{HEALTH_API_GROUP}/{HEALTH_API_VERSION}",
            "kind": HEALTH_IGNORE_RULE_KIND,
            "metadata": {
                "name": name,
                "labels": {HEALTH_IGNORE_RULE_SOURCE_LABEL: "user"},
            },
            "spec": spec,
        }
        logging(f"Creating {HEALTH_IGNORE_RULE_KIND} {name}: {spec}")
        return create_cluster_cr(
            HEALTH_API_GROUP, HEALTH_API_VERSION, HEALTH_IGNORE_RULE_PLURAL, body)

    def expire_ignore_rule(self, name):
        past = datetime.now(timezone.utc) - timedelta(minutes=1)
        logging(f"Expiring {HEALTH_IGNORE_RULE_KIND} {name}")
        return patch_cluster_cr(
            HEALTH_API_GROUP, HEALTH_API_VERSION, HEALTH_IGNORE_RULE_PLURAL, name,
            {"spec": {"expiresAt": past.strftime("%Y-%m-%dT%H:%M:%SZ")}})

    def delete_ignore_rule(self, name):
        logging(f"Deleting {HEALTH_IGNORE_RULE_KIND} {name}")
        try:
            delete_cluster_cr(
                HEALTH_API_GROUP, HEALTH_API_VERSION, HEALTH_IGNORE_RULE_PLURAL, name)
        except ApiException as e:
            if e.status != 404:
                raise
