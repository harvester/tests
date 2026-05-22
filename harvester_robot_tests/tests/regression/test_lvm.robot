*** Settings ***
Documentation    LVM Local Storage Test Cases
...             This suite tests LVM local storage feature in Harvester.
...             Ref: https://docs.harvesterhci.io/v1.8/advanced/addons/lvm-local-storage
...             Ref: https://github.com/harvester/harvester/issues/5724
Test Tags        regression    lvm    addon

Resource         ../../keywords/variables.resource
Resource         ../../keywords/common.resource
Resource         ../../keywords/storage.resource
Resource         ../../keywords/storageclass.resource
Resource         ../../keywords/addon.resource
Resource         ../../keywords/setting.resource
Resource         ../../keywords/virtualmachine.resource

Suite Setup      LVM Suite Setup
Suite Teardown   LVM Suite Teardown

*** Variables ***
${LVM_ADDON_NAME}               harvester-csi-driver-lvm
${LVM_VG_ACTIVE}                vg-dm-thin
${VG_STRIPED}                   vg-dm-striped
${LVM_SC_ACTIVE}                lvm-sc-dm-thin
${LVM_SC_STRIPED}               lvm-sc-striped
${LVM_VM_BLOCK}                 lvm-vm-block-thin
${LVM_VM_FS}                    lvm-vm-fs-thin
${LVM_VM_SC}                    lvm-vm-sc-thin
${LVM_VOL_BLOCK}                lvm-vol-block-thin
${LVM_VOL_FS}                   lvm-vol-fs-thin
${LVM_VOLUME_SIZE}              5Gi
${LVM_EXPANDED_SIZE}            10Gi

*** Test Cases ***
Test LVM Block Volume Attach And Data Integrity
    [Tags]    p0    smoke
    [Documentation]    Create LVM block volume, attach to VM, write data and verify md5sum
    ...               Steps:
    ...                   1. Create StorageClass for dm-thin volume group
    ...                   2. Create a block volume using the LVM StorageClass
    ...                   3. Create a VM
    ...                   4. Add the LVM volume to the VM
    ...                   5. Mount the disk inside VM, write data and compute md5sum
    ...               Expected Result:
    ...                   - Volume is created and attached to VM
    ...                   - Data is written and md5sum is recorded

    Given LVM StorageClass Is Created    ${LVM_SC_ACTIVE}    ${LVM_VG_ACTIVE}    ${LVM_VG_TYPE}
    And LVM Block Volume Is Created    ${LVM_VOL_BLOCK}    ${LVM_VOLUME_SIZE}    ${LVM_SC_ACTIVE}
    And VM Is Created And Running    ${LVM_VM_BLOCK}    ${IMAGE_NAME}    sc_name=${LVM_SC_ACTIVE}
    When Volume Is Attached To VM    ${LVM_VM_BLOCK}    ${LVM_VOL_BLOCK}

    ${DATA_DISK}=    Get Block Device In VM    ${LVM_VM_BLOCK}    ${LVM_VOLUME_SIZE}

    Then Data Is Written To Disk And Checksum Recorded    ${LVM_VM_BLOCK}    ${DATA_DISK}

Test LVM Filesystem Volume Attach And Data Integrity
    [Tags]    p0
    [Documentation]    Create LVM filesystem volume, attach to VM, write data and verify md5sum
    ...               Steps:
    ...                   1. Create StorageClass for dm-thin volume group
    ...                   2. Create a filesystem volume using the LVM StorageClass
    ...                   3. Create a VM
    ...                   4. Add the LVM volume to the VM
    ...                   5. Write data and compute md5sum
    ...               Expected Result:
    ...                   - Volume is created and attached to VM
    ...                   - Data is written and md5sum is recorded

    Given LVM StorageClass Is Created    ${LVM_SC_ACTIVE}    ${LVM_VG_ACTIVE}    ${LVM_VG_TYPE}
    And LVM Filesystem Volume Is Created    ${LVM_VOL_FS}    ${LVM_VOLUME_SIZE}    ${LVM_SC_ACTIVE}
    And VM Is Created And Running    ${LVM_VM_FS}    ${IMAGE_NAME}    sc_name=${LVM_SC_ACTIVE}
    When Volume Is Attached To VM    ${LVM_VM_FS}    ${LVM_VOL_FS}

    ${DATA_DISK}=    Get Block Device In VM    ${LVM_VM_FS}

    Then Data Is Written To Disk And Checksum Recorded    ${LVM_VM_FS}    ${DATA_DISK}    format_device=${False}

Test LVM Volume Direct VM Creation With StorageClass
    [Tags]    p0
    [Documentation]    Create VM directly using LVM StorageClass (vg-dm-thin) and verify data
    ...               Steps:
    ...                   1. Create StorageClass for dm-thin volume group
    ...                   2. Create VM directly using the LVM StorageClass
    ...                   3. Mount the disk inside VM, write data and compute md5sum
    ...               Expected Result:
    ...                   - VM is created with LVM volume
    ...                   - Data is written and md5sum is recorded

    Given LVM StorageClass Is Created    ${LVM_SC_ACTIVE}    ${LVM_VG_ACTIVE}    ${LVM_VG_TYPE}
    When VM Is Created with Additional Volume using SC    ${LVM_VM_SC}    ${LVM_SC_ACTIVE}    ${IMAGE_NAME}

    ${DATA_DISK}=    Get Block Device In VM    ${LVM_VM_SC}

    Then Data Is Written To Disk And Checksum Recorded    ${LVM_VM_SC}    ${DATA_DISK}    format_device=${False}

Test LVM Volume Snapshot And Restore To New VM
    [Tags]    p1    smoke
    [Documentation]    Take snapshots of running VMs, delete data, restore and verify
    ...               Steps:
    ...                   1. Take snapshots from above three VMs if running
    ...                   2. Restore snapshots to new VMs
    ...                   3. Check the data integrity on new VMs
    ...               Expected Result:
    ...                   - Snapshots are taken successfully
    ...                   - Restored VMs contain original data

    Given VM Snapshots Are Taken
    When Snapshots Are Restored To New VMs
    Then Restored VMs Have Correct Data

Test LVM Volume Snapshot Restore To Existing VM
    [Tags]    p1
    [Documentation]    Restore snapshots to existing VMs and verify data
    ...               Steps:
    ...                   1. Take snapshots from above three VMs if running
    ...                   2. Delete data from original VMs
    ...                   3. Restore to the snapshots to existing VMs
    ...                   4. Assert the data of VMs
    ...               Expected Result:
    ...                   - Existing VMs are restored with original data
    ...                   - Data integrity is verified

    Given VM Snapshots Are Taken
    AND Data Is Deleted From Test VMs
    WHEN Snapshots Are Restored To Existing VMs
    Then VMs Have Original Data After Restore

Test LVM Volume Expand Via VM Edit
    [Tags]    p1
    [Documentation]    Shut down VM, expand volume via VM edit, verify size
    ...               Steps:
    ...                   1. Shut down the VM
    ...                   2. Expand volume using VM edit
    ...                   3. Power on the VM
    ...                   4. Assert the volume size inside VM
    ...               Expected Result:
    ...                   - Volume is expanded successfully
    ...                   - VM shows correct expanded size

    Given VM Is Powered Off    ${LVM_VM_BLOCK}
    When Volume Is Expanded Via VM Edit    ${LVM_VM_BLOCK}    ${LVM_VOL_BLOCK}    ${LVM_EXPANDED_SIZE}
    And VM Is Powered On And Running    ${LVM_VM_BLOCK}
    Then Volume Size Inside VM Is Correct    ${LVM_VM_BLOCK}    ${LVM_EXPANDED_SIZE}

Test LVM Volume Expand Via Volume Edit
    [Tags]    p1
    [Documentation]    Shut down VM, expand volume via volume edit, verify size
    ...               Steps:
    ...                   1. Shut down the VM
    ...                   2. Expand volume using volume edit
    ...                   3. Power on the VM
    ...                   4. Assert the volume size inside VM
    ...               Expected Result:
    ...                   - Volume is expanded successfully
    ...                   - VM shows correct expanded size

    Given VM Is Powered Off    ${LVM_VM_FS}
    When LVM Volume Is Expanded Directly    ${LVM_VOL_FS}    ${LVM_EXPANDED_SIZE}
    And VM Is Powered On And Running    ${LVM_VM_FS}
    Then Volume Size Inside VM Is Correct    ${LVM_VM_FS}    ${LVM_EXPANDED_SIZE}


*** Keywords ***
LVM Suite Setup
    [Documentation]    Setup LVM test environment
    Set up test environment
    Suite Setup For Shared Resources
    # LVM Addon Setup
    addon.Install Addon From URL    ${LVM_ADDON_URL}
    addon.Enable Addon    ${LVM_ADDON_NAME}
    addon.Wait For Addon Enabled    ${LVM_ADDON_NAME}
    setting.Configure CSI Driver Setting For LVM
    storage.Identify And Assign LVM Disks
    storage.Create LVM Volume Groups

LVM Suite Teardown
    [Documentation]    Cleanup LVM test environment
    # Clean up LVM resources (VMs waited on, volumes, SCs, VGs) while addon is still running
    Run Keyword And Ignore Error    storage.Cleanup LVM Test Resources
    # Disable LVM addon
    Run Keyword And Ignore Error    addon.Disable Addon    ${LVM_ADDON_NAME}
    Run Keyword And Ignore Error    addon.Wait For Addon Disabled    ${LVM_ADDON_NAME}
    # Reset CSI driver setting now that addon is disabled
    Run Keyword And Ignore Error    setting.Reset CSI Driver Setting For LVM

    # Clean up shared resources (image, network) and general resources
    Suite Teardown For Shared Resources
