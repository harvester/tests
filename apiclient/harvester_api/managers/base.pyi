from __future__ import annotations
from typing import Final, NoReturn, ClassVar, Type

from .api import HarvesterAPI

DEFAULT_NAMESPACE: Final[str]


def merge_dict(src: dict, dest: dict) -> dict:
    """
    """


class BaseManager:
    support_to: ClassVar[str]

    @classmethod
    def is_support(cls, target_version: str) -> bool:
        """
        """
    @classmethod
    def for_version(cls, version: str) -> Type[BaseManager]:
        """
        """
    def __init__(self, api: HarvesterAPI) -> NoReturn:
        """
        """
    @property
    def api(self) -> HarvesterAPI:
        """
        """
