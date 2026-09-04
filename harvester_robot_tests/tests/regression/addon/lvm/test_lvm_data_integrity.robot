*** Settings ***
Documentation    LVM data-integrity coverage: volumes must survive republish
...              without reformatting, and snapshot restores must reproduce
...              the source data bit-for-bit, including explicit zero regions.
Test Tags        regression    addon    lvm    data-integrity

Resource         ../../../../keywords/lvm.resource
Resource         ../../../../keywords/workload.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown


*** Variables ***
${LVM_SC_NAME}                ${EMPTY}
${LVM_FS_VOLUME_NAME}         ${EMPTY}
${LVM_BLK_VOLUME_NAME}        ${EMPTY}
${LVM_RESTORED_VOLUME_NAME}   ${EMPTY}
${LVM_SNAPSHOT_NAME}          ${EMPTY}
${LVM_NODE_NAME}              ${EMPTY}
${PATTERN_SIZE_MB}            128


*** Test Cases ***
Republished Filesystem Volume Keeps Its Data
    [Documentation]    A Filesystem PVC is mounted by a pod, written to, then
    ...    republished by a fresh pod. The driver must detect the existing
    ...    filesystem and mount it instead of reformatting: the file written
    ...    by the first pod has to survive with an identical checksum.
    [Tags]    p1
    Create Volume
    ...    ${LVM_FS_VOLUME_NAME}
    ...    ${LVM_VOLUME_SIZE}
    ...    storage_class=${LVM_SC_NAME}
    ...    volume_mode=Filesystem
    ...    access_mode=ReadWriteOnce
    Create Workload Pod With Volume    ${POD_FS_FIRST}    ${LVM_FS_VOLUME_NAME}    Filesystem
    ${checksum}=    Write File To Filesystem Volume    ${POD_FS_FIRST}
    Delete Workload Pod    ${POD_FS_FIRST}
    Create Workload Pod With Volume    ${POD_FS_SECOND}    ${LVM_FS_VOLUME_NAME}    Filesystem
    ${checksum_after}=    Filesystem Volume File Checksum    ${POD_FS_SECOND}
    Should Be Equal    ${checksum_after}    ${checksum}
    ...    msg=Data changed across republish; the volume was likely reformatted
    Delete Workload Pod    ${POD_FS_SECOND}

Snapshot Restore Reproduces Block Data Including Zero Regions
    [Documentation]    Write a random/zero/random pattern on a Block volume,
    ...    snapshot it, scribble over the source, then restore. The restored
    ...    volume must checksum-match the pattern taken before the snapshot:
    ...    this proves restore isolation from the source and that the clone
    ...    path materializes zero regions instead of leaving stale disk
    ...    content behind.
    [Tags]    p1
    Create Volume
    ...    ${LVM_BLK_VOLUME_NAME}
    ...    ${LVM_VOLUME_SIZE}
    ...    storage_class=${LVM_SC_NAME}
    ...    volume_mode=Block
    ...    access_mode=ReadWriteOnce
    Create Workload Pod With Volume    ${POD_BLK_SOURCE}    ${LVM_BLK_VOLUME_NAME}    Block
    ${checksum}=    Write Block Pattern To Volume    ${POD_BLK_SOURCE}    ${PATTERN_SIZE_MB}
    Create Volume Snapshot    ${LVM_BLK_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}    lvm-snapshot
    Wait Until Snapshot Is Ready    ${LVM_SNAPSHOT_NAME}
    Overwrite Block Volume Head    ${POD_BLK_SOURCE}
    Restore Volume From Snapshot
    ...    ${LVM_BLK_VOLUME_NAME}
    ...    ${LVM_SNAPSHOT_NAME}
    ...    ${LVM_RESTORED_VOLUME_NAME}
    ...    storage_class=${LVM_SC_NAME}
    ...    access_mode=ReadWriteOnce
    Create Workload Pod With Volume    ${POD_BLK_RESTORED}    ${LVM_RESTORED_VOLUME_NAME}    Block
    ${restored_checksum}=    Block Volume Checksum    ${POD_BLK_RESTORED}    ${PATTERN_SIZE_MB}
    Should Be Equal    ${restored_checksum}    ${checksum}
    ...    msg=Restored data differs from the snapshotted pattern
    Delete Workload Pod    ${POD_BLK_RESTORED}
    Delete Workload Pod    ${POD_BLK_SOURCE}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    lvm-integrity
    Set Suite Variable    ${LVM_SC_NAME}                  lvm-sc-${suffix}
    Set Suite Variable    ${LVM_FS_VOLUME_NAME}           lvm-fs-${suffix}
    Set Suite Variable    ${LVM_BLK_VOLUME_NAME}          lvm-blk-${suffix}
    Set Suite Variable    ${LVM_RESTORED_VOLUME_NAME}     lvm-restored-${suffix}
    Set Suite Variable    ${LVM_SNAPSHOT_NAME}            lvm-snapshot-${suffix}
    Set Suite Variable    ${POD_FS_FIRST}                 pod-fs-a-${suffix}
    Set Suite Variable    ${POD_FS_SECOND}                pod-fs-b-${suffix}
    Set Suite Variable    ${POD_BLK_SOURCE}               pod-blk-src-${suffix}
    Set Suite Variable    ${POD_BLK_RESTORED}             pod-blk-restored-${suffix}
    ${node}=    Initialize LVM Workload Suite
    Set Suite Variable    ${LVM_NODE_NAME}    ${node}
    Create LVM Storage Class
    ...    ${LVM_SC_NAME}
    ...    ${LVM_VG_NAME}
    ...    ${LVM_VG_TYPE}
    ...    ${LVM_NODE_NAME}

Local Suite Teardown
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_FS_FIRST}
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_FS_SECOND}
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_BLK_SOURCE}
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_BLK_RESTORED}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_RESTORED_VOLUME_NAME}
    Run Keyword And Ignore Error
    ...    Delete Volume Snapshot    ${LVM_BLK_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_BLK_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_FS_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_SC_NAME}
