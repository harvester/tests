
"""
Utility functions for Harvester Robot Framework tests
Includes the shared API client accessor function
"""

import logging as log
import coloredlogs
import os
import sys
from datetime import datetime

# Global API client instance
_harvester_api_client = None

coloredlogs.install(level='INFO', fmt='%(asctime)s %(levelname)s %(message)s')
logger = log.getLogger(__name__)


def get_harvester_api_client():
    """
    Get the shared Harvester API client instance.
    """
    global _harvester_api_client    # NOQA
    if _harvester_api_client is None:
        raise RuntimeError(
            "Harvester API client not initialized. "
            "Call init_harvester_api_client() first."
        )
    caller = sys._getframe(1)
    logging(f"DEBUG: get_harvester_api_client() called \
            from {caller.f_code.co_filename}:{caller.f_lineno}")
    state = 'NONE' if _harvester_api_client is None else 'SET'
    logging(f"DEBUG: _harvester_api_client is {state}")
    return _harvester_api_client


def init_harvester_api_client(endpoint, username, password):
    """Initialize the shared Harvester API client"""
    global _harvester_api_client

    from harvester_api import create_harvester_api_client

    logging(f'Initializing Harvester API client for {endpoint}')

    _harvester_api_client = create_harvester_api_client(
        endpoint=endpoint,
        username=username,
        password=password,
        verify_ssl=False
    )

    logging('Harvester API client initialized successfully')
    return _harvester_api_client


def generate_name_with_suffix(kind, suffix):
    """Generate unique name with timestamp suffix"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    name = f"{kind}-{suffix}-{timestamp}"
    logging(f"Generated name: {name}")
    return name


def get_retry_count_and_interval():
    """Get retry count and interval from environment or defaults"""
    retry_count = int(os.getenv('RETRY_COUNT', '100'))
    retry_interval = int(os.getenv('RETRY_INTERVAL', '3'))
    return retry_count, retry_interval


def logging(message, level='INFO'):
    """Log message with specified level"""
    if level == 'DEBUG':
        logger.debug(message)
    elif level == 'INFO':
        logger.info(message)
    elif level == 'WARNING':
        logger.warning(message)
    elif level == 'ERROR':
        logger.error(message)
    else:
        logger.info(message)


def init_k8s_api_client():
    """Initialize Kubernetes API client"""
    # Suppress SSL warnings first
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    from kubernetes import client, config

    try:
        config.load_incluster_config()
        logging("Loaded in-cluster Kubernetes config", level="DEBUG")
    except Exception as e:
        msg = f"Loading Kubernetes in-cluster config didn't work, fall back to kube config: {e}"
        logging(msg, level="DEBUG")
        config.load_kube_config()
        logging("Loaded kubeconfig", level="DEBUG")

    # Disable SSL verification for self-signed certificates
    # Get the current configuration and modify it
    configuration = client.Configuration.get_default_copy()
    configuration.verify_ssl = False
    configuration.assert_hostname = False

    # Set it as the default
    client.Configuration.set_default(configuration)

    # Also create and set custom API client with SSL verification disabled
    api_client = client.ApiClient(configuration=configuration)

    logging("Kubernetes API client initialized successfully with SSL verification disabled")

    return api_client
