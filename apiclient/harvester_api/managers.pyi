from typing import Type, TypeAlias, Final, Optional, NoReturn, ClassVar, Mapping, Callable, Tuple
from pathlib import Path

from requests.models import Response

from .api import HarvesterAPI
from .models import VolumeSpec, RestoreSpec as RSpec_T, BaseSettingSpec, BackupTargetSpec, VMSpec

United_S: TypeAlias = str

DEFAULT_NAMESPACE: Final[str]


def merge_dict(src: dict, dest: dict) -> dict:
    """
    """


class BaseManager:
    def __init__(self, api: HarvesterAPI) -> NoReturn:
        """
        """
    @property
    def api(self) -> HarvesterAPI:
        """
        """


class HostManager(BaseManager):
    PATH_fmt: ClassVar[str]
    METRIC_fmt: ClassVar[str]

    def get(
        self,
        name: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def create(self, *args, **kwargs) -> NoReturn:
        """
        """
    def update(
        self,
        name: str,
        data: Mapping,
        *,
        raw: Optional[bool] = ...,
        as_json: Optional[bool] = ...,
        **kwargs
    ) -> dict | Response:
        """
        """
    def delete(
        self,
        name: str,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def get_metrics(
        self,
        name: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def maintenance_mode(
        self,
        name: str,
        enable: Optional[bool] = ...
    ) -> dict:
        """
        """


class ImageManager(BaseManager):
    PATH_fmt: ClassVar[str]
    UPLOAD_fmt: ClassVar[str]

    def create_data(
        self,
        name: str,
        url: str,
        desc: str,
        stype: str,
        namespace: str,
        display_name: str = ...
    ) -> dict:
        """
        """
    def get(
        self,
        name: str = ...,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def create(
        self,
        name: str,
        namespace: str = ...,
        **kwargs
    ) -> dict | Response:
        """
        """
    def create_by_url(
        self,
        name: str,
        url: str,
        namespace: str = ...,
        description: str = ...,
        display_name: str = ...
    ) -> dict | Response:
        """
        """
    def create_by_file(
        self,
        name: str,
        filepath: str | Path,
        namespace: str = ...,
        description: str = ...,
        display_name: str = ...
    ) -> dict | Response:
        """
        """
    def update(
        self,
        name: str,
        data: Mapping,
        *,
        raw: Optional[bool] = ...,
        as_json: Optional[bool] = ...,
        **kwargs
    ) -> dict | Response:
        """
        """
    def delete(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """


class VolumeManager(BaseManager):
    PATH_fmt: ClassVar[str]
    Spec: VolumeSpec

    def get(
        self,
        name: str = ...,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def create(
        self,
        name: str,
        volume_spec: Type[VolumeSpec],
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def update(
        self,
        name: str,
        volume_spec: Type[VolumeSpec],
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...,
        as_json: Optional[bool] = ...,
        **kwargs
    ) -> dict | Response:
        """
        """
    def delete(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """


class TemplateManager(BaseManager):
    PATH_fmt: ClassVar[str]
    VER_PATH_fmt: ClassVar[str]

    def create_data(
        self,
        name: str,
        namespace: str,
        description: str
    ) -> dict:
        """
        """
    def create_version_data(
        self,
        name: str,
        namespace: str,
        cpu: int | float | United_S,
        mem: int | float | United_S,
        disk_name: str
    ) -> dict:
        """
        """
    def get(
        self,
        name: str = ...,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def get_version(
        self,
        name: str = ...,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def create(
        self,
        name: str,
        namespace: str = ...,
        description: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def update(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...,
        **options
    ) -> dict | Response:
        """
        """
    def delete(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """


class BackupManager(BaseManager):
    BACKUP_fmt: ClassVar[str]
    RESTORE_fmt: ClassVar[str]
    RestoreSpec: RSpec_T

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
        restore_spec: Type[RSpec_T],
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


class KeypairManager(BaseManager):
    PATH_fmt: ClassVar[str]

    def create_data(
        self,
        name: str,
        namespace: str,
        public_key: str
    ) -> dict:
        """
        """
    def get(
        self,
        name: str = ...,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def create(
        self,
        name: str,
        public_key: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def update(self, *args, **kwargs) -> NoReturn:
        """
        """
    def delete(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """


class NetworkManager(BaseManager):
    PATH_fmt: ClassVar[str]
    API_VERSION: ClassVar[str]

    def create_data(
        self,
        name: str,
        namespace: str,
        vlan_id: int,
        bridge_name: str
    ) -> dict:
        """
        """
    def get(
        self,
        name: str = ...,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def create(
        self,
        name: str,
        vlan_id: int,
        namespace: str = ...,
        *,
        cluster_network: Optional[str] = ...,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def update(self, *args, **kwargs) -> NoReturn:
        """
        """
    def delete(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """


class SettingManager(BaseManager):
    vlan: ClassVar[str]
    PATH_fmt: ClassVar[str]
    Spec: BaseSettingSpec
    BackupTargetSpec: BackupTargetSpec

    def get(
        self,
        name: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def update(
        self,
        name: str,
        spec: Type[BaseSettingSpec] | Mapping,
        *,
        raw: Optional[bool] = ...,
        as_json: Optional[bool] = ...,
        **kwargs
    ) -> dict | Response:
        """
        """
    def backup_target_test_connection(
        self,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """


class SupportBundlemanager(BaseManager):
    PATH_fmt: ClassVar[str]
    DL_fmt: ClassVar[str]

    def create_data(
        self,
        name: str,
        description: str,
        issue_url: str
    ) -> dict:
        """
        """
    def get(
        self,
        uid: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def create(
        self,
        name: str,
        description: str = ...,
        issue_url: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def download(self, uid: str) -> Tuple[int, str]:
        """
        """
    def update(self, *args, **kwargs) -> NoReturn:
        """
        """
    def delete(self, uid: str, *, raw: Optional[bool] = ...) -> dict | Response:
        """
        """


class ClusterNetworkManager(BaseManager):
    PATH_fmt: ClassVar[str]
    CONFIG_fmt: ClassVar[str]

    def create_data(
        self,
        name: str,
        description: str = ...,
        labels: Optional[dict] = ...,
        annotations: Optional[dict] = ...
    ) -> dict:
        """
        """
    def create_config_data(
        self,
        name: str,
        clusternetwork: str,
        *nics: str,
        bond_mode: Optional[str] = ...,
        hostname: Optional[str] = ...,
        miimon: Optional[int] = ...,
        mtu: Optional[int] = ...
    ) -> dict:
        """
        """
    def get(
        self,
        name: str = ...,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def create(
        self,
        name: str,
        description: str = ...,
        labels: Optional[dict] = ...,
        annotations: Optional[dict] = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def update(
        self,
        name: str,
        data: Mapping,
        *,
        raw: Optional[bool] = ...,
        as_json: Optional[bool] = ...,
        **kwargs
    ) -> dict | Response:
        """
        """
    def delete(
        self,
        name: str,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def get_config(
        self,
        name: str = ...,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def create_config(
        self,
        name: str,
        clusternetwork: str,
        *nics: str,
        bond_mode: Optional[str] = ...,
        hostname: Optional[str] = ...,
        miimon: Optional[int] = ...,
        mtu: Optional[int] = ...,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """
    def update_config(
        self,
        name: str,
        data: Mapping,
        *,
        raw: Optional[bool] = ...,
        as_json: Optional[bool] = ...,
        **kwargs
    ) -> dict | Response:
        """
        """
    def delete_config(
        self,
        name: str,
        *,
        raw: Optional[bool] = ...
    ) -> dict | Response:
        """
        """


class VirtualMachineManager(BaseManager):
    API_VERSION: ClassVar[str]
    PATH_fmt: ClassVar[str]
    VMI_fmt: ClassVar[str]
    VMIOP_fmt: ClassVar[str]
    Spec: VMSpec

    def get(
        self,
        name: str = ...,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...,
        **kwargs
    ):
        """
        """
    def create(
        self,
        name: str,
        vm_spec: Type[VMSpec],
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
    def update(
        self,
        name: str,
        vm_spec: Type[VMSpec],
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...,
        as_json: Optional[bool] = ...,
        **kwargs
    ):
        """
        """
    def delete(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
    def clone(
        self,
        name: str,
        new_vm_name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
    def backup(
        self,
        name: str,
        backup_name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
    def start(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
    def restart(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
    def stop(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
    def migrate(
        self,
        name: str,
        target_node: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
    def abort_migrate(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
    def pause(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
    def unpause(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
    def softreboot(
        self,
        name: str,
        namespace: str = ...,
        *,
        raw: Optional[bool] = ...
    ):
        """
        """
