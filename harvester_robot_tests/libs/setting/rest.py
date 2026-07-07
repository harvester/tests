""" Setting Component: REST Implementation

Layer 4: Component and its implementation
"""

from .base import Base


class Rest(Base):
    """REST implementation for Setting operations using Harvester API"""

    def __init__(self):
        super().__init__()

    def get(self, setting_id):
        return super().get(setting_id)

    def enable(self, setting_id):
        return super().enable(setting_id)

    def update(self, setting_id, value):
        return super().update(setting_id, value)
