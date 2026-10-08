*** Settings ***
Documentation    Restoring an image with a custom backingImageName from the
...    backup target (harvester/harvester#11641 restore path).
...    When Harvester syncs backup-target metadata into a cluster where the
...    image no longer exists (DR), it re-creates the image with sourceType
...    restore from a backup-store URL that carries only the Longhorn
...    BackingImage name. For an image that used spec.backingImageName that
...    name must become the BackingImage and StorageClass name again
...    (GetRestoreSCName), otherwise VM backups whose PVCs reference the
...    original StorageClass cannot be restored.
...    A single cluster cannot replay the metadata sync itself: deleting
...    the image also deletes its metadata from the target. The suite
...    therefore backs the VM up (uploading the backing image), removes the
...    backup, VM and image, and creates the exact image the sync would
...    create (sourceType restore, the BackupBackingImage's URL), which
...    runs the same controller path.
...    Suite Setup ensures the cluster backup-target setting is configured
...    (see test_vm_backup.robot); the suite skips without one, and on
...    clusters whose VirtualMachineImage CRD lacks backingImageName.
Test Tags        backup    image    backingimage    virtualmachines    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/storageclass.resource
Resource    ../../../keywords/virtualmachine.resource
Resource    ../../../keywords/backup.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${IMG_NAME}         ${EMPTY}
# The custom name; doubles as the Longhorn BackingImage and StorageClass name
${BI_NAME}          ${EMPTY}
${VM_NAME}          ${EMPTY}
${BACKUP_NAME}      ${EMPTY}
${RESTORED_VM_NAME}    ${EMPTY}
# Longhorn volume names recorded from the backup before it is deleted, so the
# teardown can clean the leftover BackupVolume CRs on the backup target.
@{BACKUP_VOL_NAMES}


*** Test Cases ***
Back Up VM Using Image With Custom Backing Image Name
    [Tags]    p0
    [Documentation]    Back up the VM and wait until the image's backing image copy
    ...    on the backup target is Completed; its backup-store URL is what a
    ...    DR cluster restores the image from.
    Given VM should be running    ${VM_NAME}
    When VM backup is created    ${VM_NAME}    ${BACKUP_NAME}
    Then Backup should be ready    ${BACKUP_NAME}
    And Wait Until Backup Backing Image Is Completed    ${BI_NAME}

Image Restored From Backup Target Keeps Custom Storage Class Name
    [Tags]    p0
    [Documentation]    Remove the backup, VM and image (StorageClass and BackingImage
    ...    go with it), then create the image Harvester's metadata sync would
    ...    create: sourceType restore, spec.url from the BackupBackingImage.
    ...    Although the spec carries no backingImageName, the BackingImage and
    ...    status.storageClassName must be the custom name again, derived
    ...    from the URL's backingImage parameter.
    ${vol_names}=    Get Backup Volume Names    ${BACKUP_NAME}
    Set Suite Variable    @{BACKUP_VOL_NAMES}    @{vol_names}
    ${bbi}=    Get Backup Backing Image    ${BI_NAME}
    # The webhook refuses to delete the image while a VMBackup references its
    # StorageClass, so wait the backup out; the image is re-created under the
    # same name, so wait it out too.
    Given VM backup is deleted    ${BACKUP_NAME}
    And Backup should be deleted    ${BACKUP_NAME}
    And VM is deleted    ${VM_NAME}
    And Delete image by name    ${IMG_NAME}
    And Wait for image deleted by name    ${IMG_NAME}
    And Wait Until Storage Class Is Deleted    ${BI_NAME}
    And Wait Until Backing Image Is Deleted    ${BI_NAME}
    When Create restore image from backing image backup    ${IMG_NAME}    ${bbi}[url]    checksum=${bbi}[checksum]
    And Wait for image downloaded by name    ${IMG_NAME}
    Then Image State Is Active    ${IMG_NAME}
    And Image Storage Class Name Should Be    ${IMG_NAME}    ${BI_NAME}
    And Storage Class Is Present    ${BI_NAME}
    And Storage Class Parameter Should Be    ${BI_NAME}    backingImage    ${BI_NAME}
    And Backing Image Should Exist    ${BI_NAME}

VM Boots From Restored Image
    [Tags]    p0
    [Documentation]    The custom-named StorageClass of the restored image must
    ...    provision a bootable root disk, which is what a restored VM backup
    ...    needs from it in a DR cluster.
    Given Image State Is Active    ${IMG_NAME}
    When VM is created    ${RESTORED_VM_NAME}    ${IMG_NAME}
    Then VM should be running    ${RESTORED_VM_NAME}
    And VM qemu-agent should be connected    ${RESTORED_VM_NAME}


*** Keywords ***
Local Suite Setup
    # Set the resource names BEFORE anything that can fail or skip: the suite
    # teardown always runs, and cleaning up with still-empty names would poll
    # collection URLs for minutes (and an empty-name delete targets the whole
    # collection).
    ${suffix}=    Generate Unique Name    custom-bi
    Set Suite Variable    ${IMG_NAME}            img-${suffix}
    Set Suite Variable    ${BI_NAME}             bi-${suffix}
    Set Suite Variable    ${VM_NAME}             vm-bak-${suffix}
    Set Suite Variable    ${BACKUP_NAME}         backup-${suffix}
    Set Suite Variable    ${RESTORED_VM_NAME}    vm-restored-${suffix}
    Set up test environment
    Skip Unless Cluster Supports Custom Backing Image Name
    Backup target is configured
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}    backing_image_name=${BI_NAME}
    Image Storage Class Name Should Be    ${IMG_NAME}    ${BI_NAME}
    VM is created    ${VM_NAME}    ${IMG_NAME}
    VM should be running    ${VM_NAME}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    # Keep the failure state for debugging by cleaning up only when all tests pass.
    Run Keyword If Any Tests Failed    Log Variables
    IF    '${SUITE STATUS}' == 'PASS'
        # Backup first (it references the source VM), then VMs, then the image.
        Run Keyword And Ignore Error    VM backup is deleted    ${BACKUP_NAME}
        Run Keyword And Ignore Error    VM is deleted    ${RESTORED_VM_NAME}
        Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
        # Longhorn keeps BackupVolume/BackupBackingImage bookkeeping CRs (and
        # the matching data on the backup target) even after the VMBackup is
        # deleted. Clean ours before the image goes away — the backing image
        # lookup needs the live image CR (a restored image names it in its
        # spec.url).
        Run Keyword And Ignore Error    Cleanup Longhorn Backup Artifacts    ${BACKUP_VOL_NAMES}    ${IMG_NAME}
        Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
    END
