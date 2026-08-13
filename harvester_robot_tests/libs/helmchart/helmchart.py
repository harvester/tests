"""
HelmChart component wrapper.
Layer 4: delegates to CRD or REST implementation based on HARVESTER_OPERATION_STRATEGY.
"""
import os

from constant import HarvesterOperationStrategy, DEFAULT_TIMEOUT_LONG
from helmchart.base import Base
from helmchart.crd import CRD
from helmchart.rest import Rest


class HelmChart(Base):
    """Selects the CRD or REST implementation at construction time."""

    def __init__(self):
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        if strategy_str == HarvesterOperationStrategy.REST.value:
            self._impl = Rest()
        else:
            self._impl = CRD()

    def create(self, name, namespace, spec):
        return self._impl.create(name, namespace, spec)

    def wait_for_deployed(self, name, namespace, timeout=DEFAULT_TIMEOUT_LONG):
        return self._impl.wait_for_deployed(name, namespace, timeout)

    def delete(self, name, namespace, timeout=DEFAULT_TIMEOUT_LONG):
        return self._impl.delete(name, namespace, timeout)
