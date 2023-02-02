from typing import Type, TypeVar, TypeAlias, Optional, NoReturn, Iterable, ClassVar, Any

from requests import Session

from .managers import (
    HostManager, KeypairManager, ImageManager, SettingManager,
    NetworkManager, VolumeManager, TemplateManager, SupportBundlemanager,
    ClusterNetworkManager, VirtualMachineManager, BackupManager
)

API_T = TypeVar('API_T', bound='HarvesterAPI')
Version: TypeAlias = Any  # pkg_resources.extern.packaging.version.Version
Url: TypeAlias = str


class HarvesterAPI:
    """
    """
    API_VERSION: ClassVar[str]

    session: Session
    endpoint: Url
    hosts: Type[HostManager]
    keypairs: Type[KeypairManager]
    images: Type[ImageManager]
    networks: Type[NetworkManager]
    volumes: Type[VolumeManager]
    templates: Type[TemplateManager]
    supportbundle: Type[SupportBundlemanager]
    settings: Type[SettingManager]
    clusternetworks: Type[ClusterNetworkManager]
    vms: Type[VirtualMachineManager]
    backups: Type[BackupManager]

    @classmethod
    def login(
        cls: Type[API_T],
        endpoint: Url,
        user: str,
        passwd: str,
        session: Optional[Session] = ...,
        ssl_verify: bool = ...
    ) -> API_T:
        """
        """
    def __init__(
        self,
        endpoint: Url,
        token: Optional[str] = ...,
        session: Optional[Session] = ...
    ) -> NoReturn:
        """
        """
    @property
    def cluster_version(self) -> Version:
        """
        """
    def get_url(self,
                path: str) -> Url:
        """
        """
    def authenticate(self, user: str, passwd: str, **kwargs) -> dict:
        """
        """
    def set_retries(
        self,
        times: int = 5,
        status_forcelist: Iterable[int] = ...,
        **kwargs
    ) -> NoReturn:
        """
        """
    def generate_kubeconfig(self) -> str:
        """
        """
