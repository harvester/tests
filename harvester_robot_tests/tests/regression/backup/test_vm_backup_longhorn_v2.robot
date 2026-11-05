*** Settings ***
Documentation    VM snapshot and backup of VMs with Longhorn v2 volumes
...    - #11934 (PR #11935): snapshots are allowed, remote backups are still rejected
...    - #11970 (PR #11971): the VM API does not offer the `backup` action
...    VMs:
...    - LHv2 VM: boots from an image imported onto an LHv2 StorageClass (CDI). Its root
...      PVC is a CDI DataVolume PVC, for which the API hid `backup` already before #11971.
...    - LHv2 data VM (stopped): LHv1 root disk and a blank LHv2 data disk, no CDI PVC.
...    Stopped VMs save node memory, the API offers the actions independent of the power state.
...    The suite enables the LHv2 data engine if needed, reuses a provisioned LHv2 disk
...    (or provisions a free NVMe disk) and creates its own LHv2 StorageClass.
...    Requires a backup target and an LHv2 disk of at least 40 GiB per node: the suite
...    creates three 10 GiB volumes (image, LHv2 VM, restored VM) and a 1 GiB data disk,
...    and Longhorn also keeps 25% of the disk free. A smaller disk leaves the image
...    import stuck at 0% until the setup times out.
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
Library     pabot.PabotLib

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${LHV2_SC}             ${EMPTY}
${IMG_NAME}            ${EMPTY}
${LHV2_IMG_NAME}       ${EMPTY}
${LHV2_VM_NAME}        ${EMPTY}
${LHV2_DATA_VM_NAME}   ${EMPTY}
${SNAPSHOT_NAME}       ${EMPTY}
${RESTORED_VM_NAME}    ${EMPTY}
&{PROVISIONED_DISKS}


*** Test Cases ***
VM With LHv2 Data Volume Does Not Offer Backup Action
    [Tags]    p0    issue-11970
    [Documentation]    #11970: no CDI PVC, so the former check offered `backup`.
    ...    The stopped VM's PVCs may still be provisioning (unbound PVCs keep `backup`),
    ...    so the assertions are retried.
    Given VM should be stopped    ${LHV2_DATA_VM_NAME}
    Then Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VM should offer action    ${LHV2_DATA_VM_NAME}    snapshot
    And Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VM should not offer action    ${LHV2_DATA_VM_NAME}    backup

Backup Of LHv2 VM Is Rejected
    [Tags]    p0    issue-11934
    Given VM should be running    ${LHV2_VM_NAME}
    Then VM backup creation should be rejected    ${LHV2_VM_NAME}    backup-${LHV2_VM_NAME}
    ...    *contains Longhorn v2 volume*

Snapshot Of LHv2 VM Is Created
    [Tags]    p0    issue-11934    issue-11970
    Given VM should be running    ${LHV2_VM_NAME}
    When Snapshot is created    ${LHV2_VM_NAME}    ${SNAPSHOT_NAME}
    Then Snapshot should be ready    ${SNAPSHOT_NAME}

Snapshot Of LHv2 VM Is Restored To New VM
    [Tags]    p0    issue-11934    issue-11970
    Given Snapshot should be ready    ${SNAPSHOT_NAME}
    When Snapshot is restored to new VM    ${SNAPSHOT_NAME}    ${RESTORED_VM_NAME}
    Then VM should be running    ${RESTORED_VM_NAME}

Restored LHv2 VM Does Not Offer Backup Action
    [Tags]    p0    issue-11970
    [Documentation]    #11970 repro: the root PVC of a VM restored from a snapshot
    ...    is no CDI DataVolume PVC, so the former check offered `backup`
    Given VM should be running    ${RESTORED_VM_NAME}
    Then VM should offer action    ${RESTORED_VM_NAME}    snapshot
    And VM should not offer action    ${RESTORED_VM_NAME}    backup


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}            img-${suffix}
    Set Suite Variable    ${LHV2_IMG_NAME}       img-lhv2-${suffix}
    Set Suite Variable    ${LHV2_VM_NAME}        vm-lhv2-${suffix}
    Set Suite Variable    ${LHV2_DATA_VM_NAME}   vm-lhv2data-${suffix}
    Set Suite Variable    ${SNAPSHOT_NAME}       snap-${suffix}
    Set Suite Variable    ${RESTORED_VM_NAME}    vm-restored-${suffix}
    Set Suite Variable    ${LHV2_SC}             sc-${suffix}
    # image/rest.py and vm/rest.py ignore storage_class, extra_disks and disk_access_mode
    Skip If    '%{HARVESTER_OPERATION_STRATEGY=crd}'.lower() == 'rest'
    ...    The LHv2 setup needs the CRD operation strategy
    # Serialize with other suites using free NVMe disks, released in the teardown
    Acquire Lock    ${LHV2_DISK_LOCK}
    Set up test environment
    Backup target is configured
    ${disks}=    Create LHv2 Storage Class With Provisioned Disks    ${LHV2_SC}
    Set Suite Variable    ${PROVISIONED_DISKS}    ${disks}
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    Image is available for VM creation    ${LHV2_IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    ...    storage_class=${LHV2_SC}
    &{disk}=    Create Dictionary    size=1Gi    storage_class=${LHV2_SC}
    ...    access_mode=ReadWriteOnce
    @{disks}=    Create List    ${disk}
    VM is created    ${LHV2_DATA_VM_NAME}    ${IMG_NAME}    1    1Gi
    ...    run_strategy=Halted    extra_disks=${disks}
    VM is created    ${LHV2_VM_NAME}    ${LHV2_IMG_NAME}    1    1Gi
    ...    disk_access_mode=ReadWriteOnce
    VM should be running    ${LHV2_VM_NAME}

Local Suite Teardown
    # Always clean up: leftover VMs of a failed run occupy node memory and make
    # the next run fail as well. The details are in the robot log.
    Run Keyword If Any Tests Failed    Log Variables
    Delete Suite Resources
    Run Keyword And Ignore Error    Release Lock    ${LHV2_DISK_LOCK}

Delete Suite Resources
    # restored VM -> restore -> snapshot: the webhook blocks the reverse order
    Run Keyword And Ignore Error    VM is deleted    ${RESTORED_VM_NAME}
    Run Keyword And Ignore Error    Restore is deleted    restore-${RESTORED_VM_NAME}
    Run Keyword And Ignore Error    Snapshot is deleted    ${SNAPSHOT_NAME}
    # Only exists if the webhook regressed and accepted the negative test's backup
    Run Keyword And Ignore Error    VM backup is deleted    backup-${LHV2_VM_NAME}
    Run Keyword And Ignore Error    Backup should be deleted    backup-${LHV2_VM_NAME}
    Run Keyword And Ignore Error    VM is deleted    ${LHV2_VM_NAME}
    Run Keyword And Ignore Error    VM is deleted    ${LHV2_DATA_VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${LHV2_IMG_NAME}
    # The image is deleted asynchronously and still references the StorageClass
    Run Keyword And Ignore Error    Wait for image deleted by name    ${LHV2_IMG_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LHV2_SC}
    # host/test_longhorn_v2.robot needs unprovisioned disks, reused disks stay untouched
    Run Keyword And Ignore Error    Unprovision Storages    ${PROVISIONED_DISKS}
