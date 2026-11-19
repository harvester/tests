*** Settings ***
Documentation    Persistent Reservation Setting Test Cases
...    The persistent-reservation-enabled setting (default false) turns on
...    SCSI-3 persistent reservation in KubeVirt, which VM LUN disks with
...    `reservation: true` need (e.g. Windows Server Failover Clustering on a
...    shared SAN LUN). The setting controller always writes
...    spec.configuration.persistentReservationConfiguration.enabled in the
...    KubeVirt CR explicitly, and virt-operator then adds (or removes) the
...    pr-helper container in every virt-handler pod. The setting webhook only
...    accepts true/false and refuses to disable the setting while a VM that
...    uses a reservation LUN is running.
...    harvester/harvester#11840 (part of harvester/harvester#11834)
Test Tags        virtualmachines    settings    regression

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/setting.resource
Resource    ../../../keywords/virtualmachine.resource
Resource    ../../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# First release with the setting. Override to run the suite on a build that
# carries the feature with an older version string.
${PR_SETTING_MIN_VERSION}    1.10.0
# Block-mode PVC attached as the reservation LUN. KubeVirt only checks the
# disk definition when it admits the VM, and the guest is not asked to issue
# persistent reservation commands, so any Block-mode storage that the VM can
# start with works. To mirror a failover cluster disk, use a shareable LUN:
# Harvester only allows that on a ReadWriteMany volume from a provisioner
# other than Longhorn (e.g. a CSI SAN driver), so it is off by default.
${PR_LUN_STORAGE_CLASS}      ${DEFAULT_STORAGE_CLASS}
${PR_LUN_ACCESS_MODE}        ReadWriteMany
${PR_LUN_SHAREABLE}          ${FALSE}
# StorageClass for the test image. Empty uses the cluster default.
${IMAGE_STORAGE_CLASS}       ${EMPTY}

# Dynamic Variables
${SUPPORTED}              ${FALSE}
${ORIGINAL_PR_VALUE}      ${None}
${IMG_NAME}               ${EMPTY}
${VM_PR_REJECTED}         ${EMPTY}
${VM_PR_ADMITTED}         ${EMPTY}
${VM_PR_RUNNING}          ${EMPTY}


*** Test Cases ***
Persistent Reservation Is Disabled By Default
    [Tags]    p0
    [Documentation]    The setting exists with default false. With the default
    ...    in effect, the KubeVirt CR explicitly sets
    ...    persistentReservationConfiguration.enabled=false and the
    ...    virt-handler pods run without the pr-helper container.
    Setting Default Should Be    ${PR_SETTING_ID}    false
    Update Setting    ${PR_SETTING_ID}    ${None}
    KubeVirt Persistent Reservation Should Be    false
    Virt Handler Pods Should Have pr-helper    ${False}

Enabling The Setting Turns On Persistent Reservation In KubeVirt
    [Tags]    p0
    [Documentation]    Setting the value to true sets enabled=true in the
    ...    KubeVirt CR and rolls the virt-handler pods with a pr-helper
    ...    container. Setting it back to false writes an explicit
    ...    enabled=false and removes pr-helper again.
    Update Setting    ${PR_SETTING_ID}    true
    KubeVirt Persistent Reservation Should Be    true
    Virt Handler Pods Should Have pr-helper    ${True}
    Update Setting    ${PR_SETTING_ID}    false
    KubeVirt Persistent Reservation Should Be    false
    Virt Handler Pods Should Have pr-helper    ${False}

Setting Rejects Values Other Than True Or False
    [Tags]    p1    negative
    [Documentation]    The setting webhook only accepts boolean values, and a
    ...    rejected update leaves the setting and the KubeVirt CR unchanged.
    Update Setting    ${PR_SETTING_ID}    false
    KubeVirt Persistent Reservation Should Be    false
    FOR    ${value}    IN    yes    enabled
        ${result}=    Try To Update Setting    ${PR_SETTING_ID}    ${value}
        Operation Should Be Rejected    ${result}    must be true or false
    END
    ${value}=    Get Setting Value    ${PR_SETTING_ID}
    Should Be Equal As Strings    ${value}    false
    KubeVirt Persistent Reservation Is    false

VM With A Reservation LUN Is Rejected While Disabled
    [Tags]    p1    negative
    [Documentation]    With the setting disabled, KubeVirt refuses a VM whose
    ...    LUN disk asks for persistent reservation.
    Update Setting    ${PR_SETTING_ID}    false
    KubeVirt Persistent Reservation Should Be    false
    ${vm}=    Set Variable    ${VM_PR_REJECTED}
    ${lun}=    Reservation LUN Volume Is Created    ${vm}
    @{luns}=    Create List    ${lun}
    ${result}=    Try To Create VM    ${vm}    ${IMG_NAME}    1    2Gi
    ...    run_strategy=Halted    lun_volumes=${luns}
    # KubeVirt 1.9 says "persistent reservation is not enabled", older
    # releases "PersistentReservation feature gate is not enabled"
    Operation Should Be Rejected    ${result}    persistent reservation    PersistentReservation
    ${result}=    Try To Get VM    ${vm}
    Operation Should Be Not Found    ${result}
    [Teardown]    Run Keywords    Common Test Teardown    AND
    ...    Run Keyword And Ignore Error    Delete Volume    ${vm}-lun

VM With A Reservation LUN Starts When Enabled
    [Tags]    p1
    [Documentation]    With the setting enabled, a VM with a SCSI LUN disk
    ...    using `reservation: true` is admitted and starts.
    Update Setting    ${PR_SETTING_ID}    true
    KubeVirt Persistent Reservation Should Be    true
    Virt Handler Pods Should Have pr-helper    ${True}
    ${vm}=    Set Variable    ${VM_PR_ADMITTED}
    ${lun}=    Reservation LUN Volume Is Created    ${vm}
    @{luns}=    Create List    ${lun}
    VM is created    ${vm}    ${IMG_NAME}    1    2Gi    lun_volumes=${luns}
    VM should be running    ${vm}
    [Teardown]    Run Keywords    Common Test Teardown    AND
    ...    Run Keyword And Ignore Error    VM is deleted    ${vm}

Disabling Is Rejected While A Running VM Uses A Reservation LUN
    [Tags]    p1    negative
    [Documentation]    Disabling removes pr-helper from virt-handler, which
    ...    would break a running VM that uses a reservation LUN, so the
    ...    webhook rejects it (also as a reset to the default) until the VM
    ...    is stopped.
    Update Setting    ${PR_SETTING_ID}    true
    KubeVirt Persistent Reservation Should Be    true
    Virt Handler Pods Should Have pr-helper    ${True}
    ${vm}=    Set Variable    ${VM_PR_RUNNING}
    ${lun}=    Reservation LUN Volume Is Created    ${vm}
    @{luns}=    Create List    ${lun}
    VM is created    ${vm}    ${IMG_NAME}    1    2Gi    lun_volumes=${luns}
    VM should be running    ${vm}
    FOR    ${value}    IN    false    ${None}
        ${result}=    Try To Update Setting    ${PR_SETTING_ID}    ${value}
        Operation Should Be Rejected    ${result}    persistent reservation
    END
    KubeVirt Persistent Reservation Is    true
    VM is stopped    ${vm}
    VM should be stopped    ${vm}
    # The webhook reads VMIs from an informer cache, give it a moment
    Wait Until Keyword Succeeds    60s    ${RETRY_INTERVAL}
    ...    Update Setting    ${PR_SETTING_ID}    false
    KubeVirt Persistent Reservation Should Be    false
    [Teardown]    Run Keywords    Common Test Teardown    AND
    ...    Run Keyword And Ignore Error    VM is deleted    ${vm}


*** Keywords ***
Reservation LUN Volume Is Created
    [Arguments]    ${vm_name}
    [Documentation]    Create a Block-mode PVC named <vm>-lun and return the
    ...    `lun_volumes` entry that attaches it to the VM as a SCSI LUN with
    ...    persistent reservation.
    Create Volume    ${vm_name}-lun    1Gi    storage_class=${PR_LUN_STORAGE_CLASS}
    ...    access_mode=${PR_LUN_ACCESS_MODE}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Volume Phase Is Bound    ${vm_name}-lun
    ${lun}=    Create Dictionary    claim=${vm_name}-lun    reservation=${True}
    ...    shareable=${PR_LUN_SHAREABLE}
    RETURN    ${lun}

Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}          img-${suffix}
    Set Suite Variable    ${VM_PR_REJECTED}    vm-pr-rejected-${suffix}
    Set Suite Variable    ${VM_PR_ADMITTED}    vm-pr-admitted-${suffix}
    Set Suite Variable    ${VM_PR_RUNNING}     vm-pr-running-${suffix}
    Set up test environment
    ${supported}=    Cluster Version Is At Least    ${PR_SETTING_MIN_VERSION}
    Skip If    not ${supported}
    ...    The ${PR_SETTING_ID} setting needs Harvester v${PR_SETTING_MIN_VERSION} or later
    # Restored in the suite teardown; None means the default applies
    ${original}=    Get Setting Value    ${PR_SETTING_ID}
    Set Suite Variable    ${ORIGINAL_PR_VALUE}    ${original}
    Set Suite Variable    ${SUPPORTED}    ${TRUE}
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    ...    storage_class=${IMAGE_STORAGE_CLASS}

Restore Persistent Reservation Setting
    [Documentation]    Put back the value the setting had before the suite and
    ...    wait until KubeVirt and the virt-handler pods follow it.
    Update Setting    ${PR_SETTING_ID}    ${ORIGINAL_PR_VALUE}
    ${effective}=    Get Setting Effective Value    ${PR_SETTING_ID}
    KubeVirt Persistent Reservation Should Be    ${effective}
    ${enabled}=    Evaluate    $effective.lower() == 'true'
    Virt Handler Pods Should Have pr-helper    ${enabled}

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    # The VMs go first: the setting cannot be disabled while one of them runs
    Run Keyword And Ignore Error    VM is deleted    ${VM_PR_ADMITTED}
    Run Keyword And Ignore Error    VM is deleted    ${VM_PR_RUNNING}
    Run Keyword And Ignore Error    Delete Volume    ${VM_PR_REJECTED}-lun
    IF    ${SUPPORTED}    Restore Persistent Reservation Setting
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
