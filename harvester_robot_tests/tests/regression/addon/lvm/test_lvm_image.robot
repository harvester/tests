*** Settings ***
Documentation    LVM-backed VM images: a VM image imported onto an LVM
...              StorageClass (CDI backend) must be able to serve as a VM
...              root disk. This is the primary Harvester user flow for the
...              LVM driver and covers the CDI import path plus booting from
...              an image-backed LVM volume.
Test Tags        regression    addon    lvm    image

Resource         ../../../../keywords/lvm.resource
Resource         ../../../../keywords/snapshot.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown


*** Variables ***
${IMAGE_NAME}           ${EMPTY}
${LVM_SC_NAME}          ${EMPTY}
${LVM_VM_NAME}          ${EMPTY}
${LVM_RESTORED_VM}      ${EMPTY}
${LVM_VM_SNAPSHOT}      ${EMPTY}
${LVM_NODE_NAME}        ${EMPTY}


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

VM Snapshot Of LVM-Backed VM Restores Into A New VM
    [Documentation]    Take a Harvester VM snapshot (VirtualMachineBackup,
    ...    type snapshot) of the LVM-rooted VM and restore it into a new
    ...    VM. The restore provisions new LVM volumes from the snapshot,
    ...    and the restored guest must boot (csi-driver-lvm#64 test plan
    ...    case 2).
    [Tags]    p1
    Skip    Known Harvester limitation: restore-new never starts the target VM while its WaitForFirstConsumer volumes wait for a consumer, so the restore deadlocks (updateStatus gates VM start on isVolumesReady; WFFC PVCs bind only once the VM runs). Applies to every WFFC StorageClass incl. LVM.
    Snapshot is created    ${LVM_VM_NAME}    ${LVM_VM_SNAPSHOT}
    Snapshot should be ready    ${LVM_VM_SNAPSHOT}
    Snapshot is restored to new VM    ${LVM_VM_SNAPSHOT}    ${LVM_RESTORED_VM}
    VM should be running    ${LVM_RESTORED_VM}
    VM qemu-agent should be connected    ${LVM_RESTORED_VM}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    lvm-image
    Set Suite Variable    ${IMAGE_NAME}         image-${suffix}
    Set Suite Variable    ${LVM_SC_NAME}        lvm-sc-${suffix}
    Set Suite Variable    ${LVM_VM_NAME}        lvm-vm-${suffix}
    Set Suite Variable    ${LVM_RESTORED_VM}    lvm-restored-vm-${suffix}
    Set Suite Variable    ${LVM_VM_SNAPSHOT}    lvm-vmsnap-${suffix}
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
    # Deletions are asynchronous; wait each one out, or the StorageClass
    # deletion is denied while the image still references it and the addon
    # cannot be disabled afterwards.
    Run Keyword And Ignore Error    VM is deleted    ${LVM_RESTORED_VM}
    Run Keyword And Ignore Error    VM should be deleted    ${LVM_RESTORED_VM}
    Run Keyword And Ignore Error    Snapshot is deleted    ${LVM_VM_SNAPSHOT}
    Run Keyword And Ignore Error    Snapshot should be deleted    ${LVM_VM_SNAPSHOT}
    Run Keyword And Ignore Error    VM is deleted    ${LVM_VM_NAME}
    Run Keyword And Ignore Error    VM should be deleted    ${LVM_VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
    Run Keyword And Ignore Error    Wait for image deleted by name    ${IMAGE_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_SC_NAME}
