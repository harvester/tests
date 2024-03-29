from .base import DEFAULT_NAMESPACE
from .hosts import HostManager
from .images import ImageManager
from .volumes import VolumeManager
from .backups import BackupManager, VirtualMachineSnapshotManager
from .keypairs import KeypairManager
from .settings import SettingManager
from .networks import NetworkManager, IPPoolManager
from .templates import TemplateManager
from .supportbundles import SupportBundleManager
from .storageclasses import StorageClassManager
from .clusternetworks import ClusterNetworkManager
from .volumesnapshots import VolumeSnapshotManager
from .virtualmachines import VirtualMachineManager
# Not available in dashboard
from .internals import VersionManager, UpgradeManager, DEFAULT_HARVESTER_NAMESPACE
from .longhorns import (
    LonghornReplicaManager, LonghornVolumeManager, LonghornBackupVolumeManager,
    DEFAULT_LONGHORN_NAMESPACE
)

__all__ = [
 "HostManager",
 "ImageManager",
 "VolumeManager",
 "KeypairManager",
 "SettingManager",
 "NetworkManager", "IPPoolManager",
 "TemplateManager",
 "SupportBundleManager",
 "VolumeSnapshotManager",
 "ClusterNetworkManager",
 "VirtualMachineManager",
 "StorageClassManager",
 "BackupManager", "VirtualMachineSnapshotManager",
 "VersionManager", "UpgradeManager",
 "LonghornReplicaManager", "LonghornVolumeManager", "LonghornBackupVolumeManager",
 "DEFAULT_HARVESTER_NAMESPACE",
 "DEFAULT_NAMESPACE",
 "DEFAULT_LONGHORN_NAMESPACE"
]
