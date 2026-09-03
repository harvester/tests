*** Settings ***
Documentation    LVM block-volume provisioning and VM attachment.
Test Tags        regression    addon    lvm    volume

Resource         ../../../../keywords/lvm.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown


*** Variables ***
${LVM_DISK_NAME}    lvm-data
${IMAGE_NAME}        ${EMPTY}
${LVM_SC_NAME}       ${EMPTY}
${LVM_VOLUME_NAME}   ${EMPTY}
${LVM_VM_NAME}       ${EMPTY}
${LVM_NODE_NAME}     ${EMPTY}


*** Test Cases ***
Provision LVM Block Volume And Attach To VM
    [Tags]    p0    smoke
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


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    lvm-attach
    Set Suite Variable    ${IMAGE_NAME}         image-${suffix}
    Set Suite Variable    ${LVM_SC_NAME}        lvm-sc-${suffix}
    Set Suite Variable    ${LVM_VOLUME_NAME}    lvm-vol-${suffix}
    Set Suite Variable    ${LVM_VM_NAME}        lvm-vm-${suffix}
    ${node}=    Initialize LVM Workload Suite
    Set Suite Variable    ${LVM_NODE_NAME}    ${node}
    Image is available for VM creation    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}

Local Suite Teardown
    Run Keyword And Ignore Error    VM is deleted    ${LVM_VM_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_SC_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
