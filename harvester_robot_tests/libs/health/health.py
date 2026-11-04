"""
Health Component - delegates to CRD or REST implementation
Layer 4: Selects implementation based on strategy

The implementation is selected based on the HARVESTER_OPERATION_STRATEGY
environment variable. Valid values are 'crd' or 'rest'. Defaults to 'crd' if not set.
"""
import os

from constant import HarvesterOperationStrategy, DEFAULT_TIMEOUT
from health.base import Base
from health.crd import CRD
from health.rest import Rest


class Health(Base):
    """Health component - selects implementation by HARVESTER_OPERATION_STRATEGY"""

    def __init__(self):
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        if strategy_str == HarvesterOperationStrategy.REST.value:
            self.health = Rest()
        else:
            self.health = CRD()

    def component_health_exists(self, name):
        return self.health.component_health_exists(name)

    def get_check(self, component_health_name, check_name):
        return self.health.get_check(component_health_name, check_name)

    def wait_for_check_affects_resource(self, component_health_name, check_name,
                                        resource_name, timeout=DEFAULT_TIMEOUT):
        return self.health.wait_for_check_affects_resource(
            component_health_name, check_name, resource_name, timeout)
