*** Settings ***
Documentation    VM snapshot and backup of VMs with Longhorn v2 volumes
...    - #11934 (PR #11935): snapshots are allowed, remote backups are still rejected
...    - #11970 (PR #11971): the VM API does not offer the `backup` action
...    VMs:
...    - LHv2 VM: boots from an image imported onto an LHv2 StorageClass (CDI). Its root
...      PVC is a CDI DataVolume PVC, for which the API hid `backup` already before #11971.
...    - LHv2 data VM (stopped): LHv1 root disk and a blank LHv2 data disk, no CDI PVC.
...    - Control VM (stopped): Longhorn v1 only.
...    Stopped VMs save node memory, the API offers the actions independent of the power state.
...    The suite enables the LHv2 data engine if needed, reuses a provisioned LHv2 disk
...    (or provisions a free NVMe disk) and creates its own LHv2 StorageClass.
...    Requires a backup target.
Test Tags        backup    snapshot    virtualmachines    lhv2

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/virtualmachine.resource
Resource    ../../../keywords/snapshot.resource
Resource    ../../../keywords/backup.resource
Resource    ../../../keywords/setting.resource
Resource    ../../../keywords/storage.resource
Resource    ../../../keywords/storageclass.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${LHV2_SC}             ${EMPTY}
${IMG_NAME}            ${EMPTY}
${LHV2_IMG_NAME}       ${EMPTY}
${LHV1_VM_NAME}        ${EMPTY}
${LHV2_VM_NAME}        ${EMPTY}
${LHV2_DATA_VM_NAME}   ${EMPTY}
${SNAPSHOT_NAME}       ${EMPTY}
${RESTORED_VM_NAME}    ${EMPTY}


*** Test Cases ***
LHv1 VM Offers Backup Action
    [Tags]    p0    issue-11970
    [Documentation]    Control: with a backup target the action is offered at all
    Then VM should offer action    ${LHV1_VM_NAME}    backup

VM With LHv2 Data Volume Does Not Offer Backup Action
    [Tags]    p0    issue-11970
    [Documentation]    #11970: no CDI PVC, so the former check offered `backup`
    Then VM should offer action    ${LHV2_DATA_VM_NAME}    snapshot
    And VM should not offer action    ${LHV2_DATA_VM_NAME}    backup

LHv2 VM Offers Snapshot But Not Backup Action
    [Tags]    p0    issue-11970
    Given VM should be running    ${LHV2_VM_NAME}
    Then VM should offer action    ${LHV2_VM_NAME}    snapshot
    And VM should not offer action    ${LHV2_VM_NAME}    backup

Backup Of LHv2 VM Is Rejected
    [Tags]    p0    issue-11934
    Given VM should be running    ${LHV2_VM_NAME}
    Then Run Keyword And Expect Error    *contains Longhorn v2 volume*
    ...    VM backup is created    ${LHV2_VM_NAME}    backup-${LHV2_VM_NAME}

Snapshot Of LHv2 VM Is Created
    [Tags]    p0    issue-11934
    Given VM should be running    ${LHV2_VM_NAME}
    When Snapshot is created    ${LHV2_VM_NAME}    ${SNAPSHOT_NAME}
    Then Snapshot should be ready    ${SNAPSHOT_NAME}

Snapshot Of LHv2 VM Is Restored To New VM
    [Tags]    p0    issue-11934
    Given Snapshot should be ready    ${SNAPSHOT_NAME}
    When Snapshot is restored to new VM    ${SNAPSHOT_NAME}    ${RESTORED_VM_NAME}
    Then VM should be running    ${RESTORED_VM_NAME}

Restored LHv2 VM Does Not Offer Backup Action
    [Tags]    p0    issue-11970
    [Documentation]    #11970 repro: the root PVC of a VM restored from a snapshot
    ...    is no CDI DataVolume PVC, so the former check offered `backup`
    Given VM should be running    ${RESTORED_VM_NAME}
    Then VM should not offer action    ${RESTORED_VM_NAME}    backup


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}            img-${suffix}
    Set Suite Variable    ${LHV2_IMG_NAME}       img-lhv2-${suffix}
    Set Suite Variable    ${LHV1_VM_NAME}        vm-lhv1-${suffix}
    Set Suite Variable    ${LHV2_VM_NAME}        vm-lhv2-${suffix}
    Set Suite Variable    ${LHV2_DATA_VM_NAME}   vm-lhv2data-${suffix}
    Set Suite Variable    ${SNAPSHOT_NAME}       snap-${suffix}
    Set Suite Variable    ${RESTORED_VM_NAME}    vm-restored-${suffix}
    Set Suite Variable    ${LHV2_SC}             sc-${suffix}
    Set up test environment
    Backup target is configured
    Create LHv2 Storage Class For Suite
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    Image is available for VM creation    ${LHV2_IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    ...    storage_class=${LHV2_SC}
    Stopped VM is created    ${LHV1_VM_NAME}    ${IMG_NAME}    1    1Gi
    &{disk}=    Create Dictionary    size=1Gi    storage_class=${LHV2_SC}
    ...    access_mode=ReadWriteOnce
    @{disks}=    Create List    ${disk}
    VM is created    ${LHV2_DATA_VM_NAME}    ${IMG_NAME}    1    1Gi
    ...    run_strategy=Halted    extra_disks=${disks}
    VM is created    ${LHV2_VM_NAME}    ${LHV2_IMG_NAME}    1    1Gi
    ...    disk_access_mode=ReadWriteOnce
    VM should be running    ${LHV2_VM_NAME}

Create LHv2 Storage Class For Suite
    ${is_enabled}=    Run Keyword And Return Status    setting.LHv2 Data Engine Is Enabled
    IF    not ${is_enabled}
        setting.Enable LHv2 Data Engine
        setting.Wait Until LHv2 Data Engine Is Enabled
    END
    # Reuse provisioned LHv2 disks, provision a free NVMe disk only if there is none
    &{disk_by_node}=    storage.Get Provisioned LHv2 Disks
    IF    not $disk_by_node
        &{disk_by_node}=    storage.Get Available NVMe Disks
        Provision Storages With LHv2 Data Engine    ${disk_by_node}
    END
    Wait Until Storages Are Provisioned    ${disk_by_node}
    # No disk selector: v2 volumes only land on v2 disks anyway
    ${replicas}=    Get Length    ${disk_by_node}
    Create LHv2 Storage Class    ${LHV2_SC}    ${replicas}    ${EMPTY}

Local Suite Teardown
    # Always clean up: leftover VMs of a failed run occupy node memory and make
    # the next run fail as well. The details are in the robot log.
    Run Keyword If Any Tests Failed    Log Variables
    Delete Suite Resources

Delete Suite Resources
    # restored VM -> restore -> snapshot: the webhook blocks the reverse order
    Run Keyword And Ignore Error    VM is deleted    ${RESTORED_VM_NAME}
    Run Keyword And Ignore Error    Restore is deleted    restore-${RESTORED_VM_NAME}
    Run Keyword And Ignore Error    Snapshot is deleted    ${SNAPSHOT_NAME}
    Run Keyword And Ignore Error    VM is deleted    ${LHV2_VM_NAME}
    Run Keyword And Ignore Error    VM is deleted    ${LHV2_DATA_VM_NAME}
    Run Keyword And Ignore Error    VM is deleted    ${LHV1_VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${LHV2_IMG_NAME}
    # The image is deleted asynchronously and still references the StorageClass
    Run Keyword And Ignore Error    Wait for image deleted by name    ${LHV2_IMG_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LHV2_SC}
