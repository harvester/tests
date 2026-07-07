*** Settings ***
Documentation    VM Backup and Restore Test Cases
...    Port of harvester/tests test_4_vm_backup_restore.py TestBackupRestore
...    basic flow: backup a VM, restore it into a new VM, restore it over the
...    original VM, then delete the backup.
...    Suite Setup ensures the cluster backup-target setting is configured:
...    an existing target is used as-is, otherwise it is set from the
...    BACKUP_TARGET_NFS_ENDPOINT environment variable; the whole suite is
...    skipped when neither is available.
Test Tags        backup    virtualmachines    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/virtualmachine.resource
Resource    ../../../keywords/backup.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${IMG_NAME}                ${EMPTY}
${VM_NAME}                 ${EMPTY}
${BACKUP_NAME}             ${EMPTY}
${RESTORED_VM_NAME}        ${EMPTY}
${RESTORE_NEW_NAME}        ${EMPTY}
${RESTORE_REPLACE_NAME}    ${EMPTY}


*** Test Cases ***
Create VM Backup
    [Tags]    p0
    [Documentation]    Back up the running VM and wait until the backup is ready to use
    Given VM should be running    ${VM_NAME}
    When VM backup is created    ${VM_NAME}    ${BACKUP_NAME}
    Then Backup should be ready    ${BACKUP_NAME}

Restore Backup To New VM
    [Tags]    p0
    [Documentation]    Restore the backup into a brand-new VM and verify it runs
    Given Backup should be ready    ${BACKUP_NAME}
    When Backup is restored to new VM    ${BACKUP_NAME}    ${RESTORE_NEW_NAME}    ${RESTORED_VM_NAME}
    Then Restore should complete    ${RESTORE_NEW_NAME}
    And VM should be running    ${RESTORED_VM_NAME}

Restore Backup To Replace Original VM
    [Tags]    p0
    [Documentation]    Stop the original VM, restore the backup over it with the
    ...    previous volumes deleted, and verify it comes back running
    Given Backup should be ready    ${BACKUP_NAME}
    And VM is stopped    ${VM_NAME}
    And VM should be stopped    ${VM_NAME}
    When Backup is restored by replacing VM    ${BACKUP_NAME}    ${RESTORE_REPLACE_NAME}
    Then Restore should complete    ${RESTORE_REPLACE_NAME}
    And VM should be running    ${VM_NAME}

Delete VM Backup
    [Tags]    p0
    [Documentation]    Delete the backup and verify it is removed
    When VM backup is deleted    ${BACKUP_NAME}
    Then Backup should be deleted    ${BACKUP_NAME}


*** Keywords ***
Local Suite Setup
    Set up test environment
    Backup target is configured
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}                img-${suffix}
    Set Suite Variable    ${VM_NAME}                 vm-bak-${suffix}
    Set Suite Variable    ${BACKUP_NAME}             backup-${suffix}
    Set Suite Variable    ${RESTORED_VM_NAME}        vm-restored-${suffix}
    Set Suite Variable    ${RESTORE_NEW_NAME}        restore-new-${suffix}
    Set Suite Variable    ${RESTORE_REPLACE_NAME}    restore-replace-${suffix}
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    VM is created    ${VM_NAME}    ${IMG_NAME}
    VM should be running    ${VM_NAME}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    # Keep the failure state for debugging by cleaning up only when all tests pass.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    # Backup first (it references the source VM), then restores, VMs, image.
    Run Keyword And Ignore Error    VM backup is deleted    ${BACKUP_NAME}
    Run Keyword And Ignore Error    Restore is deleted    ${RESTORE_NEW_NAME}
    Run Keyword And Ignore Error    Restore is deleted    ${RESTORE_REPLACE_NAME}
    Run Keyword And Ignore Error    VM is deleted    ${RESTORED_VM_NAME}
    Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
