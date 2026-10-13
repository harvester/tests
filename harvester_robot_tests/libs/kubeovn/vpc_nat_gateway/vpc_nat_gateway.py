import os
from constant import HarvesterOperationStrategy
from vpc_nat_gateway.rest import Rest
from vpc_nat_gateway.crd import CRD
from vpc_nat_gateway.base import Base


class VPC_NAT_Gateway(Base):
    def __init__(self):
        # Get strategy from environment variable, default to CRD
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        try:
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            # If invalid value, default to CRD
            self._strategy = HarvesterOperationStrategy.CRD

        if self._strategy == HarvesterOperationStrategy.CRD:
            self.vpc_nat_gateway = CRD()
        else:
            self.vpc_nat_gateway = Rest()

    def get_all(self):
        return self.vpc_nat_gateway.get_all()

    def get(self, name):
        return self.vpc_nat_gateway.get(name)

    def create(self, name, **kwargs):
        return self.vpc_nat_gateway.create(name, **kwargs)

    def delete(self, name, **kwargs):
        return self.vpc_nat_gateway.delete(name, **kwargs)

    def cleanup(self):
        return self.vpc_nat_gateway.cleanup()
