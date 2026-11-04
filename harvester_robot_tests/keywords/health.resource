*** Settings ***
Documentation    Resource Health Keywords - Reusable keywords for the Resource
...              Health Dashboard (https://github.com/harvester/harvester/issues/8436).
...
...              The dashboard renders the cluster-scoped `ComponentHealth` resources
...              written by harvester-resource-health-controller. Each check under
...              `status.checks` lists the resources it affects as `<namespace>/<name>`
...              (cluster-scoped Longhorn volumes are listed by their bare name).
Library          Collections
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/health_keywords.py

*** Variables ***
${HEALTH_COMPONENT_VM}                      harvester-controller-vm
${HEALTH_COMPONENT_VOLUME}                  harvester-controller-volume
${HEALTH_COMPONENT_VMIMAGE}                 harvester-controller-vmimage
${HEALTH_COMPONENT_VMBACKUP}                harvester-controller-vmbackup

${HEALTH_CHECK_VM_NODE_SELECTOR}            VMNodeSelectorLiveMigrationUnsupported
${HEALTH_CHECK_REPLICA_SCHEDULING}          ReplicaSchedulingFailure
${HEALTH_CHECK_IMAGE_RETRY_LIMIT}           ImageRetryLimitExceeded
${HEALTH_CHECK_VMBACKUP_FAILED}             VMBackupFailed

# A URL nothing listens on, so an import fails right away.
${HEALTH_INVALID_IMAGE_URL}                 http://127.0.0.1:1/invalid.img

*** Keywords ***
Resource Health Controller Should Be Available
    [Documentation]    Skip the suite when the ComponentHealth resources are absent.
    ...    The resource health controller is not part of every Harvester release,
    ...    so clusters without it skip instead of failing.
    ${exists}=    health_keywords.Component Health Exists    ${HEALTH_COMPONENT_VM}
    IF    not ${exists}
        Skip    ComponentHealth '${HEALTH_COMPONENT_VM}' not found - resource health controller is not installed
    END
    Log    Resource health controller is available

Health Check Should Report Resource
    [Arguments]    ${component}    ${check}    ${resource}    ${severity}=${NONE}
    ...    ${message}=${NONE}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until the check of the ComponentHealth lists the resource
    ...    (formatted as `<namespace>/<name>`) as affected. Optionally assert the
    ...    check severity and that its message contains the given text.
    ${result}=    health_keywords.Wait For Health Check To Report Resource
    ...    ${component}    ${check}    ${resource}    ${timeout}
    IF    $severity is not None
        Should Be Equal    ${result}[severity]    ${severity}
    END
    IF    $message is not None
        Should Contain    ${result}[message]    ${message}
    END
    Log    Check '${check}' of '${component}' reports '${resource}': ${result}

VM Node Selector Check Should Report VM
    [Arguments]    ${vm_name}    ${namespace}=${DEFAULT_NAMESPACE}
    [Documentation]    The VM pinned by a node selector cannot live migrate, so the
    ...    VMNodeSelectorLiveMigrationUnsupported check must list it.
    Health Check Should Report Resource
    ...    ${HEALTH_COMPONENT_VM}    ${HEALTH_CHECK_VM_NODE_SELECTOR}    ${namespace}/${vm_name}
    ...    severity=Warning

Volume Replica Check Should Report Volume
    [Arguments]    ${longhorn_volume_name}
    [Documentation]    A volume whose replicas cannot be scheduled must be listed by the
    ...    ReplicaSchedulingFailure check, by its Longhorn volume (PV) name.
    Health Check Should Report Resource
    ...    ${HEALTH_COMPONENT_VOLUME}    ${HEALTH_CHECK_REPLICA_SCHEDULING}    ${longhorn_volume_name}
    ...    severity=Warning

Image Retry Limit Check Should Report Image
    [Arguments]    ${image_name}    ${namespace}=${DEFAULT_NAMESPACE}
    [Documentation]    An image whose import failed must be listed by ImageRetryLimitExceeded.
    Health Check Should Report Resource
    ...    ${HEALTH_COMPONENT_VMIMAGE}    ${HEALTH_CHECK_IMAGE_RETRY_LIMIT}    ${namespace}/${image_name}
    ...    severity=Error

VM Backup Failed Check Should Report Backup
    [Arguments]    ${backup_name}    ${namespace}=${DEFAULT_NAMESPACE}
    [Documentation]    A failed VirtualMachineBackup must be listed by VMBackupFailed.
    Health Check Should Report Resource
    ...    ${HEALTH_COMPONENT_VMBACKUP}    ${HEALTH_CHECK_VMBACKUP_FAILED}    ${namespace}/${backup_name}
    ...    severity=Error
