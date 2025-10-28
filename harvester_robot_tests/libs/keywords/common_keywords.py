
"""
Common Keywords
"""
import os
import sys

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from utility.utility import generate_name_with_suffix   # noqa E402
from utility.utility import init_harvester_api_client   # noqa E402
from utility.utility import init_k8s_api_client  # noqa E402
from utility.utility import logging  # noqa E402


class common_keywords:
    """Layer 3: Wrapper keywords - NO API client stored here!"""

    def __init__(self):
        pass

    def init_harvester_api_client(self, endpoint, username, password):
        """Initialize Harvester API client"""
        return init_harvester_api_client(endpoint, username, password)

    def init_k8s_api_client(self):
        """Initialize Kubernetes API client"""
        return init_k8s_api_client()

    def generate_name_with_suffix(self, kind, suffix):
        """Generate unique name with timestamp"""
        return generate_name_with_suffix(kind, suffix)

    def cleanup_vms(self):
        """Cleanup VMs"""
        from vm import VM
        VM().cleanup()

    def cleanup_images(self):
        """Cleanup images"""
        from image import Image
        Image().cleanup()

    def cleanup_volumes(self):
        """Cleanup volumes"""
        logging('Cleanup volumes requested')

    def cleanup_networks(self):
        """Cleanup networks"""
        logging('Cleanup networks requested')

    def cleanup_backups(self):
        """Cleanup backups"""
        logging('Cleanup backups requested')
