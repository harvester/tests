*** Settings ***
Documentation    LVM negative paths: provisioning that must fail has to fail
...              cleanly - clear pending state while alive, and no stuck PV
...              or backend leftovers after cleanup.
Test Tags        regression    addon    lvm    negative

Resource         ../../../../keywords/lvm.resource
Resource         ../../../../keywords/workload.resource
Resource         ../../../../keywords/lvm_driver.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown


*** Variables ***
${LVM_SC_NAME}                 ${EMPTY}
${LVM_SRC_VOLUME_NAME}         ${EMPTY}
${LVM_SMALL_RESTORE_NAME}      ${EMPTY}
${LVM_SNAPSHOT_NAME}           ${EMPTY}
${LVM_OUTLIVE_VOLUME_NAME}     ${EMPTY}
${LVM_OUTLIVE_SNAPSHOT_NAME}    ${EMPTY}
${LVM_NODE_NAME}               ${EMPTY}
# How long a must-not-provision PVC is observed before declaring success.
${PENDING_OBSERVATION}       60s


*** Test Cases ***
Undersized Snapshot Restore Fails And Cleans Up
    [Documentation]    Restoring a snapshot into a PVC smaller than the
    ...    snapshot size must be rejected (never bind) instead of producing
    ...    a truncated volume, and cleanup must leave no stuck PV.
    [Tags]    p1
    Create Consumed Volume    ${LVM_SRC_VOLUME_NAME}
    Create Volume Snapshot    ${LVM_SRC_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}    lvm-snapshot
    Wait Until Snapshot Is Ready    ${LVM_SNAPSHOT_NAME}
    Restore Volume From Snapshot
    ...    ${LVM_SRC_VOLUME_NAME}
    ...    ${LVM_SNAPSHOT_NAME}
    ...    ${LVM_SMALL_RESTORE_NAME}
    ...    storage_class=${LVM_SC_NAME}
    ...    access_mode=ReadWriteOnce
    ...    size=1Gi
    Create Pending Consumer Pod    ${POD_RESTORE}    ${LVM_SMALL_RESTORE_NAME}
    Sleep    ${PENDING_OBSERVATION}
    Volume Phase Is Pending    ${LVM_SMALL_RESTORE_NAME}
    Delete Workload Pod    ${POD_RESTORE}
    Delete Volume    ${LVM_SMALL_RESTORE_NAME}
    No PV Should Reference Claim    ${LVM_SMALL_RESTORE_NAME}

Snapshot Outlives Deleted Source Volume
    [Documentation]    Deleting the source volume first must not wedge the
    ...    snapshot: the VolumeSnapshot has to remain deletable afterwards,
    ...    and the backend LV must be removed as well - with the source PV
    ...    gone the driver has to resolve node/vg from its snapshot-location
    ...    record (csi-driver-lvm#64).
    [Tags]    p1
    Create Consumed Volume    ${LVM_OUTLIVE_VOLUME_NAME}    ${POD_OUTLIVE}
    Create Volume Snapshot    ${LVM_OUTLIVE_VOLUME_NAME}    ${LVM_OUTLIVE_SNAPSHOT_NAME}    lvm-snapshot
    Wait Until Snapshot Is Ready    ${LVM_OUTLIVE_SNAPSHOT_NAME}
    ${handle}=    Get Snapshot Handle    ${LVM_OUTLIVE_SNAPSHOT_NAME}
    Delete Workload Pod    ${POD_OUTLIVE}
    Delete Volume    ${LVM_OUTLIVE_VOLUME_NAME}
    Delete Volume Snapshot    ${LVM_OUTLIVE_VOLUME_NAME}    ${LVM_OUTLIVE_SNAPSHOT_NAME}
    Snapshot LV Should Not Exist On Node    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${handle}


*** Keywords ***
Create Pending Consumer Pod
    [Arguments]    ${pod_name}    ${volume_name}
    [Documentation]    Start a consumer pod without waiting for Running:
    ...    with WaitForFirstConsumer it only has to trigger provisioning,
    ...    and in these tests neither pod nor PVC is ever expected to
    ...    become ready.
    Create Workload Pod With Volume    ${pod_name}    ${volume_name}    Block    wait=${False}

Create Consumed Volume
    [Arguments]    ${volume_name}    ${pod_name}=${POD_SRC}
    ${exists}=    volume_keywords.volume_exists    ${volume_name}
    IF    ${exists}    RETURN
    Create Volume
    ...    ${volume_name}
    ...    ${LVM_VOLUME_SIZE}
    ...    storage_class=${LVM_SC_NAME}
    ...    volume_mode=Block
    ...    access_mode=ReadWriteOnce
    Create Workload Pod With Volume    ${pod_name}    ${volume_name}    Block
    Wait Until Volume Is Active    ${volume_name}

Local Suite Setup
    ${suffix}=    Generate Unique Name    lvm-negative
    Set Suite Variable    ${LVM_SC_NAME}                  lvm-sc-${suffix}
    Set Suite Variable    ${LVM_SRC_VOLUME_NAME}          lvm-src-${suffix}
    Set Suite Variable    ${LVM_SMALL_RESTORE_NAME}       lvm-small-${suffix}
    Set Suite Variable    ${LVM_SNAPSHOT_NAME}            lvm-snap-${suffix}
    Set Suite Variable    ${LVM_OUTLIVE_VOLUME_NAME}      lvm-outlive-${suffix}
    Set Suite Variable    ${LVM_OUTLIVE_SNAPSHOT_NAME}    lvm-outlive-snap-${suffix}
    Set Suite Variable    ${POD_RESTORE}                  pod-restore-${suffix}
    Set Suite Variable    ${POD_SRC}                      pod-src-${suffix}
    Set Suite Variable    ${POD_OUTLIVE}                  pod-outlive-${suffix}
    ${node}=    Initialize LVM Workload Suite
    Set Suite Variable    ${LVM_NODE_NAME}    ${node}
    Create LVM Storage Class
    ...    ${LVM_SC_NAME}
    ...    ${LVM_VG_NAME}
    ...    ${LVM_VG_TYPE}
    ...    ${LVM_NODE_NAME}

Local Suite Teardown
    Run Keyword And Ignore Error    Cleanup Workload Pods
    Run Keyword And Ignore Error
    ...    Delete Volume Snapshot    ${LVM_SRC_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}
    Run Keyword And Ignore Error
    ...    Delete Volume Snapshot    ${LVM_OUTLIVE_VOLUME_NAME}    ${LVM_OUTLIVE_SNAPSHOT_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_SMALL_RESTORE_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_OUTLIVE_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_SRC_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_SC_NAME}
