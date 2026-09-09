*** Settings ***
Documentation    LVM volume cloning: creating a new volume from an existing
...              data source must reproduce the data bit-for-bit. Cloning
...              from a PVC exercises the driver's volume-clone (full-copy)
...              path, which is distinct from the snapshot-restore path.
Test Tags        regression    addon    lvm    clone

Resource         ../../../../keywords/lvm.resource
Resource         ../../../../keywords/workload.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown


*** Variables ***
${LVM_SC_NAME}             ${EMPTY}
${LVM_SRC_VOLUME_NAME}     ${EMPTY}
${LVM_CLONE_VOLUME_NAME}    ${EMPTY}
${LVM_GROWN_VOLUME_NAME}    ${EMPTY}
${LVM_SNAPSHOT_NAME}       ${EMPTY}
${LVM_NODE_NAME}           ${EMPTY}
${PATTERN_SIZE_MB}         128


*** Test Cases ***
Cloned Volume Reproduces Source Data Including Zero Regions
    [Documentation]    Clone a Block volume directly from another PVC
    ...    (dataSource: PersistentVolumeClaim). Unlike a dm-thin snapshot
    ...    restore, this goes through the driver's full-copy clone path, so
    ...    it verifies that path reproduces random data and explicit zero
    ...    regions alike.
    [Tags]    p1
    Create Source Volume With Pattern
    ${checksum}=    Block Volume Checksum    ${POD_SRC}    ${PATTERN_SIZE_MB}
    Clone Volume From Volume
    ...    ${LVM_SRC_VOLUME_NAME}
    ...    ${LVM_CLONE_VOLUME_NAME}
    ...    storage_class=${LVM_SC_NAME}
    ...    access_mode=ReadWriteOnce
    Create Workload Pod With Volume    ${POD_CLONE}    ${LVM_CLONE_VOLUME_NAME}    Block
    ${clone_checksum}=    Block Volume Checksum    ${POD_CLONE}    ${PATTERN_SIZE_MB}
    Should Be Equal    ${clone_checksum}    ${checksum}
    ...    msg=Cloned data differs from the source volume
    Delete Workload Pod    ${POD_CLONE}
    Delete Volume    ${LVM_CLONE_VOLUME_NAME}

Restore Into Larger Volume Preserves Data And Capacity
    [Documentation]    Restoring a snapshot into a PVC larger than the
    ...    source is a legitimate grow-on-restore flow: the restored volume
    ...    must carry the snapshot data unchanged and report the larger
    ...    requested capacity.
    [Tags]    p1
    Create Source Volume With Pattern
    ${checksum}=    Block Volume Checksum    ${POD_SRC}    ${PATTERN_SIZE_MB}
    Create Volume Snapshot    ${LVM_SRC_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}    lvm-snapshot
    Wait Until Snapshot Is Ready    ${LVM_SNAPSHOT_NAME}
    Restore Volume From Snapshot
    ...    ${LVM_SRC_VOLUME_NAME}
    ...    ${LVM_SNAPSHOT_NAME}
    ...    ${LVM_GROWN_VOLUME_NAME}
    ...    storage_class=${LVM_SC_NAME}
    ...    access_mode=ReadWriteOnce
    ...    size=${LVM_EXPANDED_SIZE}
    Create Workload Pod With Volume    ${POD_GROWN}    ${LVM_GROWN_VOLUME_NAME}    Block
    ${restored_checksum}=    Block Volume Checksum    ${POD_GROWN}    ${PATTERN_SIZE_MB}
    Should Be Equal    ${restored_checksum}    ${checksum}
    ...    msg=Grow-on-restore changed the snapshot data
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Volume Size Is 10Gi    ${LVM_GROWN_VOLUME_NAME}
    Delete Workload Pod    ${POD_GROWN}
    Delete Volume    ${LVM_GROWN_VOLUME_NAME}


*** Keywords ***
Create Source Volume With Pattern
    [Documentation]    Provision the shared source volume, attach its pod,
    ...    and write the test pattern once. Idempotent within the suite.
    ${exists}=    volume_keywords.volume_exists    ${LVM_SRC_VOLUME_NAME}
    IF    ${exists}    RETURN
    Create Volume
    ...    ${LVM_SRC_VOLUME_NAME}
    ...    ${LVM_VOLUME_SIZE}
    ...    storage_class=${LVM_SC_NAME}
    ...    volume_mode=Block
    ...    access_mode=ReadWriteOnce
    Create Workload Pod With Volume    ${POD_SRC}    ${LVM_SRC_VOLUME_NAME}    Block
    Wait Until Volume Is Active    ${LVM_SRC_VOLUME_NAME}
    Write Block Pattern To Volume    ${POD_SRC}    ${PATTERN_SIZE_MB}

Local Suite Setup
    ${suffix}=    Generate Unique Name    lvm-clone
    Set Suite Variable    ${LVM_SC_NAME}              lvm-sc-${suffix}
    Set Suite Variable    ${LVM_SRC_VOLUME_NAME}      lvm-src-${suffix}
    Set Suite Variable    ${LVM_CLONE_VOLUME_NAME}    lvm-clone-${suffix}
    Set Suite Variable    ${LVM_GROWN_VOLUME_NAME}    lvm-grown-${suffix}
    Set Suite Variable    ${LVM_SNAPSHOT_NAME}        lvm-snap-${suffix}
    Set Suite Variable    ${POD_SRC}                  pod-src-${suffix}
    Set Suite Variable    ${POD_CLONE}                pod-clone-${suffix}
    Set Suite Variable    ${POD_GROWN}                pod-grown-${suffix}
    ${node}=    Initialize LVM Workload Suite
    Set Suite Variable    ${LVM_NODE_NAME}    ${node}
    Create LVM Storage Class
    ...    ${LVM_SC_NAME}
    ...    ${LVM_VG_NAME}
    ...    ${LVM_VG_TYPE}
    ...    ${LVM_NODE_NAME}

Local Suite Teardown
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_SRC}
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_CLONE}
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_GROWN}
    Run Keyword And Ignore Error
    ...    Delete Volume Snapshot    ${LVM_SRC_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_CLONE_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_GROWN_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_SRC_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_SC_NAME}
