*** Settings ***
Documentation    Resource Health Dashboard Test Cases
...              Covers https://github.com/harvester/harvester/issues/8436
...              (test plan: https://yu-jack.github.io/harvester-issue-test-plan/#harvester-8436).
...
...              The dashboard renders the `ComponentHealth` resources written by
...              harvester-resource-health-controller, so each test creates the
...              problematic resource and verifies the matching check lists it.
...
...              Skip conditions:
...                - ComponentHealth resources absent (controller not installed)
...                  -> whole suite skipped
...                - No backup target configured -> the VM backup failure test is skipped.
...                  The target must also be one that fails backups (for example a bucket
...                  with little space left), otherwise that test times out.
...
...              Not covered here: test case 6 (ScheduleVMBackup reaches max failure)
...              and test case 7 (VolumeRemoteBackup, needs a guest cluster).
Test Tags        regression    addons    resource-health

Resource         ../../../keywords/variables.resource
Resource         ../../../keywords/common.resource
Resource         ../../../keywords/image.resource
Resource         ../../../keywords/volume.resource
Resource         ../../../keywords/virtualmachine.resource
Resource         ../../../keywords/host.resource
Resource         ../../../keywords/storageclass.resource
Resource         ../../../keywords/backup.resource
Resource         ../../../keywords/support_bundle.resource
Resource         ../../../keywords/health.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown
Test Teardown    Health Test Teardown    ${IGNORE_RULE}


*** Variables ***
# Dynamic Variables
${IMAGE_NAME}           ${EMPTY}
${NODE_NAME}            ${EMPTY}
${VM_NODE_SELECTOR}     ${EMPTY}
${SC_REPLICA}           ${EMPTY}
${VOL_REPLICA}          ${EMPTY}
${VM_REPLICA}           ${EMPTY}
${IMAGE_BAD_A}          ${EMPTY}
${IMAGE_BAD_B}          ${EMPTY}
${IGNORE_RULE}          ${EMPTY}
${VM_BACKUP}            ${EMPTY}
${BACKUP_NAME}          ${EMPTY}
${SUPPORT_BUNDLE}       ${EMPTY}


*** Test Cases ***
Test VM With Node Selector Is Reported
    [Tags]    p0    coretest
    [Documentation]    Test case 1 of the test plan: a VM with a node selector cannot
    ...    live migrate, so the dashboard shows a VMNodeSelectorLiveMigrationUnsupported
    ...    check for it.
    Given VM is created    ${VM_NODE_SELECTOR}    ${IMAGE_NAME}    node_name=${NODE_NAME}
    And VM should be running    ${VM_NODE_SELECTOR}
    Then VM Node Selector Check Should Report VM    ${VM_NODE_SELECTOR}

Test VM With Insufficient Volume Replicas Is Reported
    [Tags]    p0
    [Documentation]    Test case 2: a storage class asks for more replicas than there are
    ...    nodes, so the replicas of a VM's volume cannot be scheduled and the dashboard
    ...    reports ReplicaSchedulingFailure for the volume.
    ${replicas}=    Given Create Storage Class With Replicas Exceeding Node Count    ${SC_REPLICA}
    And Create Volume    ${VOL_REPLICA}    1Gi    storage_class=${SC_REPLICA}    replicas=${replicas}
    When VM is created with existing volume    ${VM_REPLICA}    ${IMAGE_NAME}    ${VOL_REPLICA}
    ${pv_name}=    Get Volume PV Name    ${VOL_REPLICA}
    Then Volume Replica Check Should Report Volume    ${pv_name}

Test Image With Wrong URL Is Reported
    [Tags]    p0
    [Documentation]    Test case 3: an image with an invalid download URL fails, and the
    ...    dashboard reports ImageRetryLimitExceeded for it.
    When Create image from url with name    ${IMAGE_BAD_A}    ${HEALTH_INVALID_IMAGE_URL}    retry=${0}
    Then Image Retry Limit Check Should Report Image    ${IMAGE_BAD_A}

Test VM Backup With Insufficient Space Is Reported
    [Tags]    p1    backup
    [Documentation]    Test case 4: the backup bucket has little space left, so a VM backup
    ...    fails and the dashboard reports VMBackupFailed for it.
    Given Backup target is configured
    And VM is created    ${VM_BACKUP}    ${IMAGE_NAME}
    And VM should be running    ${VM_BACKUP}
    When VM backup is created    ${VM_BACKUP}    ${BACKUP_NAME}
    Then VM Backup Failed Check Should Report Backup    ${BACKUP_NAME}

Test Generating Support Bundle Is Reported
    [Tags]    p1
    [Documentation]    Test case 5: while a support bundle is generating, the dashboard
    ...    shows the Info check SupportBundleGenerating for it.
    When Support bundle is created    ${SUPPORT_BUNDLE}
    Then Support Bundle Generating Check Should Report Bundle    ${SUPPORT_BUNDLE}

Test Ignore A Single Resource Of A Check
    [Tags]    p1
    [Documentation]    Test case 8.1: ignoring selected resources marks only those resources
    ...    as ignored; the other resources of the check stay active.
    Given Failing Image Is Reported    ${IMAGE_BAD_A}
    And Failing Image Is Reported    ${IMAGE_BAD_B}
    When Image Check Resources Are Ignored    ${IGNORE_RULE}    ${IMAGE_BAD_A}
    Then Image Should Be Marked Ignored    ${IMAGE_BAD_A}
    And Image Should Be Marked Ignored    ${IMAGE_BAD_B}    ${False}

Test Ignore An Entire Check
    [Tags]    p1
    [Documentation]    Test case 8.2: ignoring the entire check marks the whole check as ignored.
    Given Failing Image Is Reported    ${IMAGE_BAD_A}
    When Image Check Resources Are Ignored    ${IGNORE_RULE}
    Then Image Check Should Be Marked Ignored

*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMAGE_NAME}           image-${suffix}
    Set Suite Variable    ${VM_NODE_SELECTOR}     vm-node-selector-${suffix}
    Set Suite Variable    ${SC_REPLICA}           sc-replica-${suffix}
    Set Suite Variable    ${VOL_REPLICA}          vol-replica-${suffix}
    Set Suite Variable    ${VM_REPLICA}           vm-replica-${suffix}
    Set Suite Variable    ${IMAGE_BAD_A}          image-bad-a-${suffix}
    Set Suite Variable    ${IMAGE_BAD_B}          image-bad-b-${suffix}
    Set Suite Variable    ${IGNORE_RULE}          ignore-${suffix}
    Set Suite Variable    ${VM_BACKUP}            vm-backup-${suffix}
    Set Suite Variable    ${BACKUP_NAME}          backup-${suffix}
    Set Suite Variable    ${SUPPORT_BUNDLE}       bundle-${suffix}
    Set up test environment
    Resource Health Controller Should Be Available
    ${node}=    Get node 0
    Set Suite Variable    ${NODE_NAME}    ${node}
    Image is available for VM creation    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    Health Ignore Rule Is Deleted    ${IGNORE_RULE}
    Run Keyword And Ignore Error    VM backup is deleted    ${BACKUP_NAME}
    Run Keyword And Ignore Error    Support bundle is deleted    ${SUPPORT_BUNDLE}
    Run Keyword And Ignore Error    VM is deleted    ${VM_NODE_SELECTOR}
    Run Keyword And Ignore Error    VM is deleted    ${VM_REPLICA}
    Run Keyword And Ignore Error    VM is deleted    ${VM_BACKUP}
    Run Keyword And Ignore Error    Delete Volume    ${VOL_REPLICA}
    Run Keyword And Ignore Error    Delete Storage Class    ${SC_REPLICA}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_BAD_A}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_BAD_B}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
