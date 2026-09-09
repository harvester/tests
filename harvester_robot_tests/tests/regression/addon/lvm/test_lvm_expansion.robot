*** Settings ***
Documentation    LVM volume offline expansion: capacity must grow and the
...              existing data must survive, for both Block and Filesystem
...              volume modes.
Test Tags        regression    addon    lvm    expand

Resource         ../../../../keywords/lvm.resource
Resource         ../../../../keywords/workload.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown


*** Variables ***
${LVM_DISK_NAME}         lvm-expanded-data
${IMAGE_NAME}            ${EMPTY}
${LVM_SC_NAME}           ${EMPTY}
${LVM_VOLUME_NAME}       ${EMPTY}
${LVM_BLK_DATA_VOLUME}    ${EMPTY}
${LVM_FS_DATA_VOLUME}     ${EMPTY}
${LVM_VM_NAME}           ${EMPTY}
${LVM_NODE_NAME}         ${EMPTY}


*** Test Cases ***
Expand LVM Block Volume
    [Tags]    p1
    Create LVM Storage Class
    ...    ${LVM_SC_NAME}
    ...    ${LVM_VG_NAME}
    ...    ${LVM_VG_TYPE}
    ...    ${LVM_NODE_NAME}
    VM is created    ${LVM_VM_NAME}    ${IMAGE_NAME}    node_name=${LVM_NODE_NAME}
    VM should be running    ${LVM_VM_NAME}
    Create Volume
    ...    ${LVM_VOLUME_NAME}
    ...    ${LVM_VOLUME_SIZE}
    ...    storage_class=${LVM_SC_NAME}
    ...    volume_mode=Block
    ...    access_mode=ReadWriteOnce
    Add Volume To VM    ${LVM_VM_NAME}    ${LVM_DISK_NAME}    ${LVM_VOLUME_NAME}
    Wait Until Volume Is Active    ${LVM_VOLUME_NAME}
    Volume Should Be Hotplugged    ${LVM_VM_NAME}    ${LVM_DISK_NAME}
    Remove Volume From VM    ${LVM_VM_NAME}    ${LVM_DISK_NAME}
    Volume Should Be Unplugged    ${LVM_VM_NAME}    ${LVM_DISK_NAME}
    Update Volume Size to 10Gi    ${LVM_VOLUME_NAME}
    Add Volume To VM    ${LVM_VM_NAME}    ${LVM_DISK_NAME}    ${LVM_VOLUME_NAME}
    Volume Should Be Hotplugged    ${LVM_VM_NAME}    ${LVM_DISK_NAME}
    Wait Until Volume Is Active    ${LVM_VOLUME_NAME}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Volume Size Is 10Gi    ${LVM_VOLUME_NAME}

Expanded Block Volume Keeps Its Data
    [Documentation]    Offline-expand a Block volume that already carries
    ...    data: unpublish (delete the pod), resize, republish with a fresh
    ...    pod. The written region must checksum-match and the volume must
    ...    report the new capacity.
    [Tags]    p1
    Create Volume
    ...    ${LVM_BLK_DATA_VOLUME}
    ...    ${LVM_VOLUME_SIZE}
    ...    storage_class=${LVM_SC_NAME}
    ...    volume_mode=Block
    ...    access_mode=ReadWriteOnce
    Create Workload Pod With Volume    ${POD_BLK_A}    ${LVM_BLK_DATA_VOLUME}    Block
    ${checksum}=    Write Block Pattern To Volume    ${POD_BLK_A}
    Delete Workload Pod    ${POD_BLK_A}
    Update Volume Size to 10Gi    ${LVM_BLK_DATA_VOLUME}
    Create Workload Pod With Volume    ${POD_BLK_B}    ${LVM_BLK_DATA_VOLUME}    Block
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Volume Size Is 10Gi    ${LVM_BLK_DATA_VOLUME}
    ${checksum_after}=    Block Volume Checksum    ${POD_BLK_B}
    Should Be Equal    ${checksum_after}    ${checksum}
    ...    msg=Block expansion changed the existing data
    Delete Workload Pod    ${POD_BLK_B}

Expanded Filesystem Volume Keeps Its Data And Grows
    [Documentation]    Offline-expand a Filesystem volume with a data file:
    ...    after republish the file must checksum-match and the mounted
    ...    filesystem must report the grown capacity, proving the driver
    ...    resized the filesystem and not just the LV.
    [Tags]    p1
    Create Volume
    ...    ${LVM_FS_DATA_VOLUME}
    ...    ${LVM_VOLUME_SIZE}
    ...    storage_class=${LVM_SC_NAME}
    ...    volume_mode=Filesystem
    ...    access_mode=ReadWriteOnce
    Create Workload Pod With Volume    ${POD_FS_A}    ${LVM_FS_DATA_VOLUME}    Filesystem
    ${checksum}=    Write File To Filesystem Volume    ${POD_FS_A}
    ${capacity_before}=    Filesystem Volume Capacity In MB    ${POD_FS_A}
    Delete Workload Pod    ${POD_FS_A}
    Update Volume Size to 10Gi    ${LVM_FS_DATA_VOLUME}
    Create Workload Pod With Volume    ${POD_FS_B}    ${LVM_FS_DATA_VOLUME}    Filesystem
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Volume Size Is 10Gi    ${LVM_FS_DATA_VOLUME}
    ${checksum_after}=    Filesystem Volume File Checksum    ${POD_FS_B}
    Should Be Equal    ${checksum_after}    ${checksum}
    ...    msg=Filesystem expansion changed the existing data
    ${capacity_after}=    Filesystem Volume Capacity In MB    ${POD_FS_B}
    Should Be True    ${capacity_after} > ${capacity_before}
    ...    msg=Filesystem did not grow after expansion (before ${capacity_before}MB, after ${capacity_after}MB)
    Delete Workload Pod    ${POD_FS_B}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    lvm-expansion
    Set Suite Variable    ${IMAGE_NAME}            image-${suffix}
    Set Suite Variable    ${LVM_SC_NAME}           lvm-sc-${suffix}
    Set Suite Variable    ${LVM_VOLUME_NAME}       lvm-vol-${suffix}
    Set Suite Variable    ${LVM_BLK_DATA_VOLUME}    lvm-blkdata-${suffix}
    Set Suite Variable    ${LVM_FS_DATA_VOLUME}     lvm-fsdata-${suffix}
    Set Suite Variable    ${POD_BLK_A}             pod-blk-a-${suffix}
    Set Suite Variable    ${POD_BLK_B}             pod-blk-b-${suffix}
    Set Suite Variable    ${POD_FS_A}              pod-fs-a-${suffix}
    Set Suite Variable    ${POD_FS_B}              pod-fs-b-${suffix}
    Set Suite Variable    ${LVM_VM_NAME}           lvm-vm-${suffix}
    ${node}=    Initialize LVM Workload Suite
    Set Suite Variable    ${LVM_NODE_NAME}    ${node}
    Image is available for VM creation    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}

Local Suite Teardown
    Run Keyword And Ignore Error    VM is deleted    ${LVM_VM_NAME}
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_BLK_A}
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_BLK_B}
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_FS_A}
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_FS_B}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_BLK_DATA_VOLUME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_FS_DATA_VOLUME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_SC_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
