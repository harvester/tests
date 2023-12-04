from __future__ import annotations
from typing import NoReturn, Optional, Type
from typing_extensions import override


class BaseSettingSpec:
    """
    """

    data: dict

    def __init__(self, data: dict) -> NoReturn:
        """
        """
    def to_dict(self) -> dict:
        """
        """
    @classmethod
    def from_dict(cls: Type[BaseSettingSpec], data: dict) -> BaseSettingSpec:
        """
        """


class BackupTargetSpec(BaseSettingSpec):
    """
    """

    value: Optional[dict]

    def __init__(self, value: Optional[dict] = ...) -> NoReturn:
        """
        """
    @property
    def type(self) -> str | None:
        """
        """
    def clear(self) -> NoReturn:
        """
        """
    def to_dict(self) -> dict:
        """
        """
    @override
    @classmethod
    def from_dict(cls: Type[BackupTargetSpec], data: dict) -> BackupTargetSpec:
        """
        """
    @classmethod
    def S3(
        cls: Type[BackupTargetSpec],
        bucket: str,
        region: str,
        access_id: str,
        access_secret,
        endpoint: str = ...,
        virtual_hosted: Optional[bool] = ...
    ) -> Type[BackupTargetSpec]:
        """
        """
    @classmethod
    def NFS(cls: Type[BackupTargetSpec], endpoint: str) -> Type[BackupTargetSpec]:
        """
        """
