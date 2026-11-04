*** Settings ***
Documentation    Resource Health Keywords - Reusable keywords for the Resource
...              Health Dashboard (https://github.com/harvester/harvester/issues/8436).
...
...              The dashboard renders the cluster-scoped `ComponentHealth` resources
...              written by harvester-resource-health-controller. Each check under
...              `status.checks` lists the resources it affects as `<namespace>/<name>`
...              (cluster-scoped Longhorn volumes are listed by their bare name).
...              Ignoring a check creates a cluster-scoped `HealthIgnoreRule`; the
...              controller then marks the check or the resource with `ignored: true`.
Library          Collections
Resource         variables.resource
Resource         common.resource
Resource         image.resource
Library          ../libs/keywords/health_keywords.py

*** Variables ***
${HEALTH_COMPONENT_VM}                      harvester-controller-vm
${HEALTH_COMPONENT_VOLUME}                  harvester-controller-volume
${HEALTH_COMPONENT_VMIMAGE}                 harvester-controller-vmimage
${HEALTH_COMPONENT_VMBACKUP}                harvester-controller-vmbackup
${HEALTH_COMPONENT_SUPPORTBUNDLE}           harvester-controller-supportbundle

${HEALTH_CHECK_VM_NODE_SELECTOR}            VMNodeSelectorLiveMigrationUnsupported
${HEALTH_CHECK_REPLICA_SCHEDULING}          ReplicaSchedulingFailure
${HEALTH_CHECK_IMAGE_RETRY_LIMIT}           ImageRetryLimitExceeded
${HEALTH_CHECK_VMBACKUP_FAILED}             VMBackupFailed
${HEALTH_CHECK_SUPPORTBUNDLE_GENERATING}    SupportBundleGenerating

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

Support Bundle Generating Check Should Report Bundle
    [Arguments]    ${bundle_name}    ${namespace}=harvester-system
    [Documentation]    A generating SupportBundle must be listed by the Info check SupportBundleGenerating.
    Health Check Should Report Resource
    ...    ${HEALTH_COMPONENT_SUPPORTBUNDLE}    ${HEALTH_CHECK_SUPPORTBUNDLE_GENERATING}    ${namespace}/${bundle_name}
    ...    severity=Info

Failing Image Is Reported
    [Arguments]    ${image_name}
    [Documentation]    Create the image from an invalid URL (unless it already exists) and
    ...    wait until ImageRetryLimitExceeded lists it. retry=0 fails the import at once.
    ${exists}=    Run Keyword And Return Status    Image Should Exist    ${image_name}
    IF    not ${exists}
        Create image from url with name    ${image_name}    ${HEALTH_INVALID_IMAGE_URL}    retry=${0}
    END
    Image Retry Limit Check Should Report Image    ${image_name}

Image Check Resources Are Ignored
    [Arguments]    ${rule_name}    @{image_names}
    [Documentation]    Ignore only the given images in the ImageRetryLimitExceeded check.
    ...    With no image given the entire check is ignored.
    @{resources}=    Create List
    FOR    ${image_name}    IN    @{image_names}
        Append To List    ${resources}    ${DEFAULT_NAMESPACE}/${image_name}
    END
    health_keywords.Create Health Ignore Rule    ${rule_name}
    ...    ${HEALTH_COMPONENT_VMIMAGE}    ${HEALTH_CHECK_IMAGE_RETRY_LIMIT}    ${resources}
    ...    reason=robot test

Image Should Be Marked Ignored
    [Arguments]    ${image_name}    ${ignored}=${True}
    [Documentation]    Wait until the image is (or is no longer) marked ignored in the check.
    health_keywords.Wait For Health Resource Ignored State
    ...    ${HEALTH_COMPONENT_VMIMAGE}    ${HEALTH_CHECK_IMAGE_RETRY_LIMIT}
    ...    ${DEFAULT_NAMESPACE}/${image_name}    ${ignored}    ${WAIT_TIMEOUT}

Image Check Should Be Marked Ignored
    [Arguments]    ${ignored}=${True}
    [Documentation]    Wait until the whole ImageRetryLimitExceeded check is (or is no longer) ignored.
    health_keywords.Wait For Health Check Ignored State
    ...    ${HEALTH_COMPONENT_VMIMAGE}    ${HEALTH_CHECK_IMAGE_RETRY_LIMIT}    ${ignored}    ${WAIT_TIMEOUT}

Health Ignore Rule Is Deleted
    [Arguments]    ${rule_name}
    [Documentation]    Delete the rule, ignoring when it is already gone.
    health_keywords.Delete Health Ignore Rule    ${rule_name}

Health Test Teardown
    [Arguments]    ${ignore_rule_name}
    [Documentation]    An ignore rule left behind would hide checks from the following
    ...    tests, so always delete this suite's rule before the common teardown.
    Run Keyword And Ignore Error    Health Ignore Rule Is Deleted    ${ignore_rule_name}
    Common Test Teardown
