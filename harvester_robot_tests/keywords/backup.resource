*** Settings ***
Documentation    VM Backup and Restore Keywords
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/backup_keywords.py


*** Keywords ***
Backup target is configured
    [Documentation]    Ensure the cluster backup-target setting is configured.
    ...    Uses the already-configured target when present; otherwise configures
    ...    the NFS endpoint from ${BACKUP_TARGET_NFS_ENDPOINT}. Skips when neither
    ...    is available. The setting is never reset afterwards, and all backup
    ...    suites configure the same endpoint from the same environment variable,
    ...    so concurrent (pabot) suite setups stay parallel-safe.
    ${target}=    backup_keywords.get_backup_target
    ${endpoint}=    Evaluate    $target.get('endpoint', '')
    IF    $endpoint
        Log    Backup target already configured: ${target}
    ELSE IF    $BACKUP_TARGET_NFS_ENDPOINT
        backup_keywords.set_nfs_backup_target    ${BACKUP_TARGET_NFS_ENDPOINT}
        Backup target endpoint should be    ${BACKUP_TARGET_NFS_ENDPOINT}
    ELSE
        Skip    backup-target is not configured and BACKUP_TARGET_NFS_ENDPOINT is not set; skipping backup tests
    END

Backup target endpoint should be
    [Arguments]    ${endpoint}
    [Documentation]    Assert the backup-target setting points at the given endpoint
    ${target}=    backup_keywords.get_backup_target
    Should Be Equal    ${target}[endpoint]    ${endpoint}

VM backup is created
    [Arguments]    ${vm_name}    ${backup_name}
    [Documentation]    Create a backup of the VM
    backup_keywords.create_backup    ${vm_name}    ${backup_name}

Backup should be ready
    [Arguments]    ${backup_name}
    [Documentation]    Wait until the backup is ready to use
    backup_keywords.wait_for_backup_ready    ${backup_name}

VM backup is deleted
    [Arguments]    ${backup_name}
    [Documentation]    Delete a backup
    backup_keywords.delete_backup    ${backup_name}

Backup should be deleted
    [Arguments]    ${backup_name}
    [Documentation]    Wait until the backup is removed
    backup_keywords.wait_for_backup_deleted    ${backup_name}

Backup is restored to new VM
    [Arguments]    ${backup_name}    ${restore_name}    ${new_vm_name}
    [Documentation]    Restore the backup into a brand-new VM
    backup_keywords.restore_backup_to_new_vm    ${backup_name}    ${restore_name}    ${new_vm_name}

Backup is restored by replacing VM
    [Arguments]    ${backup_name}    ${restore_name}    ${delete_volumes}=${TRUE}
    [Documentation]    Restore the backup over its (stopped) source VM
    backup_keywords.restore_backup_replace_vm    ${backup_name}    ${restore_name}    ${delete_volumes}

Restore should complete
    [Arguments]    ${restore_name}
    [Documentation]    Wait until the restore reports complete
    backup_keywords.wait_for_restore_completed    ${restore_name}

Restore is deleted
    [Arguments]    ${restore_name}
    [Documentation]    Delete a restore bookkeeping object
    backup_keywords.delete_restore    ${restore_name}

Get Backup Volume Names
    [Arguments]    ${backup_name}
    [Documentation]    Return the longhorn volume names recorded in the backup.
    ...    Capture this BEFORE deleting the backup — it is the only place the
    ...    mapping to the leftover longhorn BackupVolume CRs lives.
    ${names}=    backup_keywords.get_backup_volume_names    ${backup_name}
    RETURN    ${names}

Cleanup Longhorn Backup Artifacts
    [Arguments]    ${volume_names}    ${image_name}
    [Documentation]    Delete the longhorn BackupVolume/BackupBackingImage CRs
    ...    this suite left on the backup target (longhorn then removes the
    ...    corresponding data from the store). Only CRs matching the given
    ...    volumes/image are touched, so this stays parallel-safe. Must run
    ...    while the image CR still exists.
    backup_keywords.cleanup_longhorn_backup_artifacts    ${volume_names}    ${image_name}
