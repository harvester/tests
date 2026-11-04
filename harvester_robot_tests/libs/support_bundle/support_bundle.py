"""
SupportBundle Component - delegates to CRD or REST implementation
Layer 4: Selects implementation based on strategy

The implementation is selected based on the HARVESTER_OPERATION_STRATEGY
environment variable. Valid values are 'crd' or 'rest'. Defaults to 'crd' if not set.
"""
import os

from constant import HarvesterOperationStrategy, HARVESTER_NAMESPACE
from support_bundle.base import Base
from support_bundle.crd import CRD
from support_bundle.rest import Rest


class SupportBundle(Base):
    """SupportBundle component - selects implementation by HARVESTER_OPERATION_STRATEGY"""

    def __init__(self):
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        if strategy_str == HarvesterOperationStrategy.REST.value:
            self.support_bundle = Rest()
        else:
            self.support_bundle = CRD()

    def create(self, name, description, namespace=HARVESTER_NAMESPACE):
        return self.support_bundle.create(name, description, namespace)

    def delete(self, name, namespace=HARVESTER_NAMESPACE):
        return self.support_bundle.delete(name, namespace)
