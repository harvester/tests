from typing import Type, TypeVar, TypeAlias, Final, Optional, NoReturn, ClassVar, Iterable, List

RS_T = TypeVar("RS_T", bound="RestoreSpec")
VS_T = TypeVar("VS_T", bound="VolumeSpec")
VM_T = TypeVar("VM_T", bound="VMSpec")
SS_T = TypeVar("SS_T", bound="BaseSettingSpec")
United_S: TypeAlias = str

MGMT_NETID: Final[object]
DEFAULT_STORAGE_CLS: Final[str]


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
        cls: Type[RS_T],
        vm_name: str,
        namespace: Optional[str] = ...
    ) -> RS_T:
        """
        """
    @classmethod
    def for_existing(cls: Type[RS_T], delete_volumes: Optional[bool] = ...) -> RS_T:
        """
        """


class VMSpec:
    """
    """

    cpu_sockets: ClassVar[int]
    cpu_threads: ClassVar[int]
    run_strategy: ClassVar[str]
    eviction_strategy: ClassVar[str]
    hostname: ClassVar[str]
    machine_type: ClassVar[str]
    usbtablet: ClassVar[bool]

    cpu_cores: int
    memory: int | United_S
    description: str
    reserved_mem: int | float | United_S
    os_type: Optional[str]
    networks: List[dict]

    def __init__(
        self,
        cpu_cores: int,
        memory: int | United_S,
        description: str = ...,
        reserved_mem: int | float | United_S = ...,
        os_type: str = ...,
        mgmt_network: Optional[bool] = ...,
        guest_agent: Optional[bool] = ...
    ) -> NoReturn:
        """
        """
    @property
    def mgmt_network(self) -> bool:
        """
        """
    @mgmt_network.setter
    def mgmt_network(self, enable: bool) -> NoReturn:
        """
        """
    @property
    def acpi(self) -> bool | None:
        """
        """
    @acpi.setter
    def acpi(self, enable: bool) -> NoReturn:
        """
        """
    @property
    def efi_boot(self) -> bool:
        """
        """
    @efi_boot.setter
    def efi_boot(self, enable: bool) -> NoReturn:
        """
        """
    @property
    def secure_boot(self) -> bool:
        """
        """
    @secure_boot.setter
    def secure_boot(self, enable: bool) -> NoReturn:
        """
        """
    @property
    def guest_agent(self) -> bool:
        """
        """
    @guest_agent.setter
    def guest_agent(self, enable: bool) -> NoReturn:
        """
        """
    @property
    def user_data(self) -> str:
        """
        """
    @user_data.setter
    def user_data(self, val: str) -> NoReturn:
        """
        """
    @property
    def network_data(self) -> str:
        """
        """
    @network_data.setter
    def network_data(self, val: str) -> NoReturn:
        """
        """
    def add_cd_rom(
        self,
        name: str,
        image_id: str,
        size: int | float | United_S = ...,
        bus: str = ...
    ) -> dict:
        """
        """
    def add_image(
        self,
        name: str,
        image_id: str,
        size: int | float | United_S = ...,
        bus: str = ...,
        type: str = ...
    ) -> dict:
        """
        """
    def add_container(
        self,
        name: str,
        docker_image: str,
        bus: str = ...,
        type: str = ...
    ) -> dict:
        """
        """
    def add_volume(
        self,
        name: str,
        size: int | float | United_S,
        type: str = ...,
        bus: str = ...,
        storage_cls: str = ...
    ) -> dict:
        """
        """
    def add_existing_volume(
        self,
        name: str,
        volume_name: str,
        type: str = ...
    ) -> dict:
        """
        """
    def add_network(
        self,
        name: str,
        net_uid: str,
        model: str = ...,
        mac_addr: Optional[str] = ...
    ) -> dict:
        """
        """
    def to_dict(
        self,
        name: str,
        namespace: str,
        hostname: str = ...
    ) -> dict:
        """
        """
    @classmethod
    def from_dict(cls: Type[VM_T], data: dict) -> VM_T:
        """
        """


class VolumeSpec:
    """
    """

    volume_mode: ClassVar[str]

    access_modes: Iterable[str]
    size: int | float | United_S
    storage_cls: str
    description: str
    annotations: dict

    def __init__(
        self,
        size: int | float | United_S,
        storage_cls: Optional[str] = ...,
        description: Optional[str] = ...,
        annotations: Optional[dict] = ...
    ) -> NoReturn:
        """
        """
    def to_dict(
        self,
        name: str,
        namespace: str,
        image_id: Optional[str] = ...
    ) -> dict:
        """
        """
    @classmethod
    def from_dict(cls: Type[VS_T], data: dict) -> VS_T:
        """
        """


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
    def from_dict(cls: Type[SS_T], data: dict) -> SS_T:
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
    @classmethod
    def from_dict(cls: Type[SS_T], data: dict) -> SS_T:
        """
        """
    @classmethod
    def S3(
        cls: Type[SS_T],
        bucket: str,
        region: str,
        access_id: str,
        access_secret,
        endpoint: str = ...,
        virtual_hosted: Optional[bool] = ...
    ) -> SS_T:
        """
        """
    @classmethod
    def NFS(cls: Type[SS_T], endpoint: str) -> SS_T:
        """
        """
