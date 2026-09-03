*** Settings ***
Documentation    LVM block-volume snapshot and restore.
Test Tags        regression    addon    lvm    snapshot

Resource         ../../../../keywords/lvm.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown


*** Variables ***
${LVM_SOURCE_DISK}      lvm-source-data
${LVM_RESTORED_DISK}    lvm-restored-data
${IMAGE_NAME}                 ${EMPTY}
${LVM_SC_NAME}                ${EMPTY}
${LVM_VOLUME_NAME}            ${EMPTY}
${LVM_RESTORED_VOLUME_NAME}   ${EMPTY}
${LVM_SNAPSHOT_NAME}          ${EMPTY}
${LVM_VM_NAME}                ${EMPTY}
${LVM_NODE_NAME}              ${EMPTY}


*** Test Cases ***
Snapshot And Restore LVM Block Volume
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
    Add Volume To VM    ${LVM_VM_NAME}    ${LVM_SOURCE_DISK}    ${LVM_VOLUME_NAME}
    Wait Until Volume Is Active    ${LVM_VOLUME_NAME}
    Volume Should Be Hotplugged    ${LVM_VM_NAME}    ${LVM_SOURCE_DISK}
    Remove Volume From VM    ${LVM_VM_NAME}    ${LVM_SOURCE_DISK}
    Volume Should Be Unplugged    ${LVM_VM_NAME}    ${LVM_SOURCE_DISK}
    Create Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}    lvm-snapshot
    Wait Until Snapshot Is Ready    ${LVM_SNAPSHOT_NAME}
    Restore Volume From Snapshot
    ...    ${LVM_VOLUME_NAME}
    ...    ${LVM_SNAPSHOT_NAME}
    ...    ${LVM_RESTORED_VOLUME_NAME}
    ...    storage_class=${LVM_SC_NAME}
    ...    volume_mode=Block
    ...    access_mode=ReadWriteOnce
    Add Volume To VM    ${LVM_VM_NAME}    ${LVM_RESTORED_DISK}    ${LVM_RESTORED_VOLUME_NAME}
    Wait Until Volume Is Active    ${LVM_RESTORED_VOLUME_NAME}
    Volume Should Be Hotplugged    ${LVM_VM_NAME}    ${LVM_RESTORED_DISK}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    lvm-snapshot
    Set Suite Variable    ${IMAGE_NAME}                   image-${suffix}
    Set Suite Variable    ${LVM_SC_NAME}                  lvm-sc-${suffix}
    Set Suite Variable    ${LVM_VOLUME_NAME}              lvm-vol-${suffix}
    Set Suite Variable    ${LVM_RESTORED_VOLUME_NAME}     lvm-restored-${suffix}
    Set Suite Variable    ${LVM_SNAPSHOT_NAME}            lvm-snapshot-${suffix}
    Set Suite Variable    ${LVM_VM_NAME}                  lvm-vm-${suffix}
    ${node}=    Initialize LVM Workload Suite
    Set Suite Variable    ${LVM_NODE_NAME}    ${node}
    Image is available for VM creation    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}

Local Suite Teardown
    Run Keyword And Ignore Error    VM is deleted    ${LVM_VM_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_RESTORED_VOLUME_NAME}
    Run Keyword And Ignore Error
    ...    Delete Volume Snapshot    ${LVM_VOLUME_NAME}    ${LVM_SNAPSHOT_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_SC_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
