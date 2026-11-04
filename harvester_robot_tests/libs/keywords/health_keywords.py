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
