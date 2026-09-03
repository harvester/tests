*** Settings ***
Documentation    LVM-backed VM images: a VM image imported onto an LVM
...              StorageClass (CDI backend) must be able to serve as a VM
...              root disk. This is the primary Harvester user flow for the
...              LVM driver and covers the CDI import path plus booting from
...              an image-backed LVM volume.
Test Tags        regression    addon    lvm    image

Resource         ../../../../keywords/lvm.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown


*** Variables ***
${IMAGE_NAME}       ${EMPTY}
${LVM_SC_NAME}      ${EMPTY}
${LVM_VM_NAME}      ${EMPTY}
${LVM_NODE_NAME}    ${EMPTY}


*** Test Cases ***
VM Boots From LVM-Backed Image
    [Documentation]    Import a VM image onto the LVM StorageClass, create a
    ...    VM whose root disk is provisioned from that image, and verify the
    ...    guest actually boots (qemu-agent connects), proving the CDI
    ...    import produced a usable root volume on LVM.
    [Tags]    p1
    VM is created    ${LVM_VM_NAME}    ${IMAGE_NAME}    node_name=${LVM_NODE_NAME}
    VM should be running    ${LVM_VM_NAME}
    VM qemu-agent should be connected    ${LVM_VM_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    lvm-image
    Set Suite Variable    ${IMAGE_NAME}     image-${suffix}
    Set Suite Variable    ${LVM_SC_NAME}    lvm-sc-${suffix}
    Set Suite Variable    ${LVM_VM_NAME}    lvm-vm-${suffix}
    ${node}=    Initialize LVM Workload Suite
    Set Suite Variable    ${LVM_NODE_NAME}    ${node}
    Create LVM Storage Class
    ...    ${LVM_SC_NAME}
    ...    ${LVM_VG_NAME}
    ...    ${LVM_VG_TYPE}
    ...    ${LVM_NODE_NAME}
    # The image lands on the LVM StorageClass through the CDI backend.
    Image is available for VM creation    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}    storage_class=${LVM_SC_NAME}

Local Suite Teardown
    Run Keyword And Ignore Error    VM is deleted    ${LVM_VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_SC_NAME}
