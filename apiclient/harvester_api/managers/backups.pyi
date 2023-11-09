from typing import ClassVar, Optional, Callable, Type

from requests.models import Response

from harvester_api.models.backups import RestoreSpec
from .base import BaseManager


class BackupManager(BaseManager):
    BACKUP_fmt: ClassVar[str]
    RESTORE_fmt: ClassVar[str]
    RestoreSpec: Type[RestoreSpec]

    def get(
        self,
        name: str = ...,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...,
        **kwargs
    ) -> dict | Response:
        """
        """
    def create(
        self,
        name: str,
        restore_spec: Type[RestoreSpec],
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...,
        **kwargs
    ) -> dict | Response:
        """
        """
    def delete(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...,
        **kwargs
    ) -> dict | Response:
        """
        """
    restore: Callable
