""" ConfigMap Component

Layer 4: Component - selects the implementation by HARVESTER_OPERATION_STRATEGY
"""

import os

from constant import HarvesterOperationStrategy
from configmap.base import Base
from configmap.crd import CRD
from configmap.rest import Rest


class ConfigMap(Base):

    def __init__(self):
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        try:
            strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            strategy = HarvesterOperationStrategy.CRD

        self.configmap = Rest() if strategy == HarvesterOperationStrategy.REST else CRD()

    def create(self, name, namespace, labels=None, data=None):
        return self.configmap.create(name, namespace, labels, data)

    def delete(self, name, namespace):
        return self.configmap.delete(name, namespace)
