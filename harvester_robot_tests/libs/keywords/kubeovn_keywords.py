"""
KubeOVN General Keywords
"""

import os
import sys

# Add the path to the utility module
sys.path.insert(0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../kubeovn'))) # noqa E402
from utility.utility import logging  # noqa E402
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG  # noqa E402


class kubeovn_keywords:
    def cleanup_vpc_nat_gateways(self):
        from kubeovn import VPC_NAT_Gateway # noqa E402
        VPC_NAT_Gateway().cleanup()
