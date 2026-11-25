"""
ConfigMap Keywords - creates ConfigMap() instance and delegates - NO direct API calls!
"""

import os
import sys

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))) # noqa E402
from configmap import ConfigMap # noqa E402


class configmap_keywords:
    """ConfigMap keyword wrapper - creates ConfigMap component and delegates"""

    def __init__(self):
        self.configmap = ConfigMap()

    def create_config_map(self, name, namespace, labels=None, data=None):
        """Create a config map with optional extra labels and data"""
        self.configmap.create(name, namespace, labels, data)

    def delete_config_map(self, name, namespace):
        """Delete a config map (no-op when it does not exist)"""
        self.configmap.delete(name, namespace)
