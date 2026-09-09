*** Settings ***
Documentation    LVM snapshot lifecycle behind the CSI facade: backend LV
...              cleanup on the node, and the driver's snapshot-location
...              records added by harvester/csi-driver-lvm#64 (per-snapshot
...              ConfigMap with node/vg, used to resolve pre-provisioned
...              snapshot contents that carry only the opaque handle).
Test Tags        regression    addon    lvm    snapshot-lifecycle

Resource         ../../../../keywords/lvm.resource
Resource         ../../../../keywords/workload.resource
Resource         ../../../../keywords/lvm_driver.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown


*** Variables ***
${LVM_SC_NAME}              ${EMPTY}
${LVM_VOLUME_NAME}          ${EMPTY}
${LVM_SNAPSHOT_NAME}        ${EMPTY}
${LVM_IMPORTED_SNAPSHOT}    ${EMPTY}
${LVM_RETAIN_CLASS}         ${EMPTY}
${LVM_NODE_NAME}            ${EMPTY}
${POD_CONSUMER}             ${EMPTY}


*** Test Cases ***
Deleted Snapshot Removes Backend LV
    [Documentation]    A deleted VolumeSnapshot must remove the backing
    ...    lvm-<handle> LV on the node; a leftover would leak VG space
    ...    silently.
    [Tags]    p1
    Create Consumed Volume    ${LVM_VOLUME_NAME}
    Create Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}    lvm-snapshot
    Wait Until Snapshot Is Ready    ${LVM_SNAPSHOT_NAME}
    ${handle}=    Get Snapshot Handle    ${LVM_SNAPSHOT_NAME}
    Snapshot LV Should Exist On Node    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${handle}
    Delete Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}
    Snapshot LV Should Not Exist On Node    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${handle}

Snapshot Lifecycle Maintains Location Record
    [Documentation]    Creating a snapshot must record its backend location
    ...    (node/vg) in the driver's ConfigMap store; deleting the snapshot
    ...    must remove the record again.
    [Tags]    p1
    Create Consumed Volume    ${LVM_VOLUME_NAME}
    Create Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}    lvm-snapshot
    Wait Until Snapshot Is Ready    ${LVM_SNAPSHOT_NAME}
    ${handle}=    Get Snapshot Handle    ${LVM_SNAPSHOT_NAME}
    Snapshot Location Record Should Exist    ${handle}    ${LVM_NODE_NAME}    ${LVM_VG_NAME}
    Delete Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}
    Snapshot Location Record Should Not Exist    ${handle}

Imported Snapshot Deletes Backend Via Location Record
    [Documentation]    Retain-policy snapshot is released (objects deleted,
    ...    LV kept), then re-imported as a pre-provisioned content WITHOUT
    ...    node/vg annotations. Deleting the imported snapshot must still
    ...    remove the backend LV: the driver has to resolve the location
    ...    from its ConfigMap record.
    [Tags]    p1
    Create Consumed Volume    ${LVM_VOLUME_NAME}
    Create Retain Volume Snapshot Class    ${LVM_RETAIN_CLASS}
    Create Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}    ${LVM_RETAIN_CLASS}
    Wait Until Snapshot Is Ready    ${LVM_SNAPSHOT_NAME}
    ${handle}=    Release Snapshot Keeping Backend LV    ${LVM_SNAPSHOT_NAME}
    Snapshot LV Should Exist On Node    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${handle}
    Import Pre-Provisioned Snapshot    ${LVM_IMPORTED_SNAPSHOT}    ${handle}    ${LVM_VOLUME_SIZE}
    Wait Until Snapshot Is Ready    ${LVM_IMPORTED_SNAPSHOT}
    Delete Imported Snapshot And Wait For Backend Cleanup    ${LVM_IMPORTED_SNAPSHOT}
    Snapshot LV Should Not Exist On Node    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${handle}

Deleting A Middle Snapshot Keeps Others Restorable
    [Documentation]    Take three snapshots of the same volume at different
    ...    data states, delete the middle one, and verify the neighbours are
    ...    unaffected: their backend LVs survive and the oldest one still
    ...    restores its original data.
    [Tags]    p1
    Create Consumed Volume    ${LVM_VOLUME_NAME}
    ${checksum_a}=    Write Block Pattern To Volume    ${POD_CONSUMER}
    Create Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAP_A}    lvm-snapshot
    Wait Until Snapshot Is Ready    ${LVM_SNAP_A}
    Overwrite Block Volume Head    ${POD_CONSUMER}
    Create Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAP_B}    lvm-snapshot
    Wait Until Snapshot Is Ready    ${LVM_SNAP_B}
    Overwrite Block Volume Head    ${POD_CONSUMER}
    Create Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAP_C}    lvm-snapshot
    Wait Until Snapshot Is Ready    ${LVM_SNAP_C}
    ${handle_a}=    Get Snapshot Handle    ${LVM_SNAP_A}
    ${handle_b}=    Get Snapshot Handle    ${LVM_SNAP_B}
    ${handle_c}=    Get Snapshot Handle    ${LVM_SNAP_C}
    Delete Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAP_B}
    Snapshot LV Should Not Exist On Node    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${handle_b}
    Snapshot LV Should Exist On Node    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${handle_a}
    Snapshot LV Should Exist On Node    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${handle_c}
    Restore Volume From Snapshot
    ...    ${LVM_VOLUME_NAME}
    ...    ${LVM_SNAP_A}
    ...    ${LVM_MULTI_RESTORE}
    ...    storage_class=${LVM_SC_NAME}
    ...    access_mode=ReadWriteOnce
    Create Workload Pod With Volume    ${POD_MULTI}    ${LVM_MULTI_RESTORE}    Block
    ${restored_checksum}=    Block Volume Checksum    ${POD_MULTI}
    Should Be Equal    ${restored_checksum}    ${checksum_a}
    ...    msg=Restore from the oldest snapshot changed after deleting a newer one
    Delete Workload Pod    ${POD_MULTI}
    Delete Volume    ${LVM_MULTI_RESTORE}
    Delete Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAP_A}
    Delete Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAP_C}


*** Keywords ***
Create Consumed Volume
    [Arguments]    ${volume_name}
    [Documentation]    Create a Block PVC and attach a pod so WaitForFirstConsumer
    ...    binding provisions the backend LV. Idempotent within the suite.
    ${exists}=    volume_keywords.volume_exists    ${volume_name}
    IF    ${exists}    RETURN
    Create Volume
    ...    ${volume_name}
    ...    ${LVM_VOLUME_SIZE}
    ...    storage_class=${LVM_SC_NAME}
    ...    volume_mode=Block
    ...    access_mode=ReadWriteOnce
    Create Workload Pod With Volume    ${POD_CONSUMER}    ${volume_name}    Block
    Wait Until Volume Is Active    ${volume_name}

Local Suite Setup
    ${suffix}=    Generate Unique Name    lvm-lifecycle
    Set Suite Variable    ${LVM_SC_NAME}              lvm-sc-${suffix}
    Set Suite Variable    ${LVM_VOLUME_NAME}          lvm-vol-${suffix}
    Set Suite Variable    ${LVM_SNAPSHOT_NAME}        lvm-snap-${suffix}
    Set Suite Variable    ${LVM_IMPORTED_SNAPSHOT}    lvm-imported-${suffix}
    Set Suite Variable    ${LVM_RETAIN_CLASS}         lvm-retain-${suffix}
    Set Suite Variable    ${LVM_SNAP_A}               lvm-snap-a-${suffix}
    Set Suite Variable    ${LVM_SNAP_B}               lvm-snap-b-${suffix}
    Set Suite Variable    ${LVM_SNAP_C}               lvm-snap-c-${suffix}
    Set Suite Variable    ${LVM_MULTI_RESTORE}        lvm-multi-restore-${suffix}
    Set Suite Variable    ${POD_CONSUMER}             pod-consumer-${suffix}
    Set Suite Variable    ${POD_MULTI}                pod-multi-${suffix}
    ${node}=    Initialize LVM Workload Suite
    Set Suite Variable    ${LVM_NODE_NAME}    ${node}
    Create LVM Storage Class
    ...    ${LVM_SC_NAME}
    ...    ${LVM_VG_NAME}
    ...    ${LVM_VG_TYPE}
    ...    ${LVM_NODE_NAME}

Local Suite Teardown
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_CONSUMER}
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_MULTI}
    Run Keyword And Ignore Error
    ...    Delete Imported Snapshot And Wait For Backend Cleanup    ${LVM_IMPORTED_SNAPSHOT}
    Run Keyword And Ignore Error
    ...    Delete Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}
    Run Keyword And Ignore Error
    ...    Delete Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAP_A}
    Run Keyword And Ignore Error
    ...    Delete Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAP_B}
    Run Keyword And Ignore Error
    ...    Delete Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAP_C}
    Run Keyword And Ignore Error    Delete Volume Snapshot Class    ${LVM_RETAIN_CLASS}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_MULTI_RESTORE}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_SC_NAME}
