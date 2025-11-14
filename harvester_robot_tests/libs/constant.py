"""
Constants for Harvester test framework
"""

from enum import Enum


# Operation Strategy
class HarvesterOperationStrategy(Enum):
    """Strategy for Harvester operations - REST API or CRD"""
    REST = "rest"
    CRD = "crd"


# Harvester API Groups
HARVESTER_API_GROUP = "harvesterhci.io"
HARVESTER_API_VERSION = "v1beta1"
KUBEVIRT_API_GROUP = "kubevirt.io"
KUBEVIRT_API_VERSION = "v1"

# Harvester Namespace
HARVESTER_NAMESPACE = "harvester-system"
DEFAULT_NAMESPACE = "default"

# Harvester Resource Plurals
VIRTUALMACHINE_PLURAL = "virtualmachines"
VIRTUALMACHINEIMAGE_PLURAL = "virtualmachineimages"
VIRTUALMACHINEINSTANCE_PLURAL = "virtualmachineinstances"
VOLUME_PLURAL = "volumes"
PERSISTENTVOLUMECLAIM_PLURAL = "persistentvolumeclaims"

# Test Labels
LABEL_TEST = "harvesterhci.io/test"
LABEL_TEST_VALUE = "robot-framework"

# Size Constants
KIBIBYTE = 1024
MEBIBYTE = (KIBIBYTE * KIBIBYTE)
GIBIBYTE = (MEBIBYTE * KIBIBYTE)

# VM States
VM_STATE_STOPPED = "Stopped"
VM_STATE_RUNNING = "Running"
VM_STATE_STARTING = "Starting"
VM_STATE_STOPPING = "Stopping"
VM_STATE_MIGRATING = "Migrating"

# Volume States
VOLUME_STATE_BOUND = "Bound"
VOLUME_STATE_PENDING = "Pending"

# Image States
IMAGE_STATE_ACTIVE = "Active"
IMAGE_STATE_IMPORTING = "Importing"
IMAGE_STATE_FAILED = "Failed"

# VM Frontend Types
VOLUME_FRONTEND_BLOCKDEV = "blockdev"
VOLUME_FRONTEND_ISCSI = "iscsi"

# Access Modes
ACCESS_MODE_RWO = "ReadWriteOnce"
ACCESS_MODE_RWX = "ReadWriteMany"
ACCESS_MODE_ROX = "ReadOnlyMany"

# Image Source Types
IMAGE_SOURCE_DOWNLOAD = "download"
IMAGE_SOURCE_UPLOAD = "upload"
IMAGE_SOURCE_EXPORT = "export-from-volume"

# Network Types
NETWORK_TYPE_VLAN = "vlan"
NETWORK_TYPE_UNTAGGED = "untagged"

# Annotations
ANNOT_REPLICA_NAMES = "harvesterhci.io/replica-names"
ANNOT_DATA_CHECKSUM = "test.harvesterhci.io/data-checksum-"
ANNOT_LAST_CHECKSUM = "test.harvesterhci.io/last-recorded-checksum"
ANNOT_DESCRIPTION = "field.cattle.io/description"

# VM Run Strategies
RUN_STRATEGY_ALWAYS = "Always"
RUN_STRATEGY_HALTED = "Halted"
RUN_STRATEGY_MANUAL = "Manual"
RUN_STRATEGY_RERUN_ON_FAILURE = "RerunOnFailure"

# Storage Class
DEFAULT_STORAGE_CLASS = "longhorn"

# Retry and Timeout Defaults
DEFAULT_RETRY_COUNT = 100
DEFAULT_RETRY_INTERVAL = 3

# Timeout constants (in seconds)
DEFAULT_TIMEOUT_SHORT = 300
DEFAULT_TIMEOUT = 600
DEFAULT_TIMEOUT_LONG = 1500
