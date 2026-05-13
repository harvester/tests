""" Setting Component: REST Implementation

Layer 4: Component and its implementation
"""

from utility.utility import get_harvester_api_client
from .base import Base


class Rest(Base):
    """REST implementation for Setting operations using Harvester API"""

    def __init__(self):
        self.api_client = get_harvester_api_client()
        self.port_forward_process = None
