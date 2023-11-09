from __future__ import annotations
from typing import Optional, NoReturn, Type


class RestoreSpec:
    """
    """
    new_vm: str
    vm_name: str
    namespace: str
    delete_volumes: bool

    def __init__(
        self,
        new_vm: str,
        vm_name: Optional[str] = ...,
        namespace: Optional[str] = ...,
        delete_volumes: Optional[bool] = ...
    ) -> NoReturn:
        """
        """
    def to_dict(
        self,
        name: str,
        namespace: str,
        existing_vm: str
    ) -> dict:
        """
        """
    @classmethod
    def for_new(
        cls,
        vm_name: str,
        namespace: Optional[str] = ...
    ) -> Type[RestoreSpec]:
        """
        """
    @classmethod
    def for_existing(cls, delete_volumes: Optional[bool] = ...) -> Type[RestoreSpec]:
        """
        """
