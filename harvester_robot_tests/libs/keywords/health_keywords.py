"""
Health Keywords for Robot Framework
Layer 3: Keyword wrappers - creates Health component and delegates
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))  # noqa: E402

from utility.utility import logging  # noqa: E402
from health import Health  # noqa: E402
from constant import DEFAULT_TIMEOUT  # noqa: E402


class health_keywords:
    """Health keyword wrapper - creates Health component and delegates"""

    def __init__(self):
        self.health = Health()

    def component_health_exists(self, name):
        """Check whether a ComponentHealth resource exists"""
        logging(f'Checking ComponentHealth {name} exists')
        return self.health.component_health_exists(name)

    def wait_for_health_check_to_report_resource(self, component_health_name, check_name,
                                                 resource_name, timeout=DEFAULT_TIMEOUT):
        """Wait until the check of a ComponentHealth lists the resource as affected"""
        logging(f'Waiting for check {check_name} of {component_health_name} '
                f'to report {resource_name}')
        return self.health.wait_for_check_affects_resource(
            component_health_name, check_name, resource_name, timeout)

    def wait_for_health_resource_ignored_state(self, component_health_name, check_name,
                                               resource_name, ignored,
                                               timeout=DEFAULT_TIMEOUT):
        """Wait until a resource listed by the check is (not) marked ignored"""
        logging(f'Waiting for {resource_name} of check {check_name} to be ignored={ignored}')
        return self.health.wait_for_resource_ignored_state(
            component_health_name, check_name, resource_name, ignored, timeout)

    def wait_for_health_check_ignored_state(self, component_health_name, check_name,
                                            ignored, timeout=DEFAULT_TIMEOUT):
        """Wait until the whole check is (not) marked ignored"""
        logging(f'Waiting for check {check_name} to be ignored={ignored}')
        return self.health.wait_for_check_ignored_state(
            component_health_name, check_name, ignored, timeout)

    def create_health_ignore_rule(self, name, component_health_name, check_name,
                                  resources=None, expires_at=None, reason=None):
        """Create a HealthIgnoreRule, the same object the dashboard creates"""
        return self.health.create_ignore_rule(
            name, component_health_name, check_name, resources, expires_at, reason)

    def expire_health_ignore_rule(self, name):
        """Set the expiry of a HealthIgnoreRule to a past time"""
        return self.health.expire_ignore_rule(name)

    def delete_health_ignore_rule(self, name):
        """Delete a HealthIgnoreRule, ignoring when it is already gone"""
        return self.health.delete_ignore_rule(name)
