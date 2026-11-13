"""
KubeOVN VPC NAT Gateway Keywords
"""

import os
import sys

# Add the path to the utility module
sys.path.insert(0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../kubeovn'))) # noqa E402
from utility.utility import logging  # noqa E402
from kubeovn import VPC_NAT_Gateway # noqa E402
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG  # noqa E402


class kubeovn_vpc_nat_gateway_keywords:
    """
    KubeOVN VPC NAT Gateway keyword wrapper
    """
    def __init__(self):
        self._gw = None

    @property
    def vpc_nat_gateway(self):
        if self._gw is None:
            self._gw = VPC_NAT_Gateway()
        return self._gw

    def get_all_vpc_nat_gateways(self):
        return self.vpc_nat_gateway.get_all()

    def get_vpc_nat_gateway(self, name):
        """
        Get KubeOVN VPC NAT Gateway
        """
        return self.vpc_nat_gateway.get(name)

    def create_vpc_nat_gateway(self, name, **kwargs):
        return self.vpc_nat_gateway.create(name, **kwargs)

    def delete_vpc_nat_gateway(self, name):
        return self.vpc_nat_gateway.delete(name)
