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
Resource         ../../../keywords/virtualmachine.resource
Resource         ../../../keywords/host.resource
Resource         ../../../keywords/health.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown
Test Teardown    Common Test Teardown


*** Variables ***
# Dynamic Variables
${IMAGE_NAME}           ${EMPTY}
${NODE_NAME}            ${EMPTY}
${VM_NODE_SELECTOR}     ${EMPTY}


*** Test Cases ***
Test VM With Node Selector Is Reported
    [Tags]    p0    coretest
    [Documentation]    Test case 1 of the test plan: a VM with a node selector cannot
    ...    live migrate, so the dashboard shows a VMNodeSelectorLiveMigrationUnsupported
    ...    check for it.
    Given VM is created    ${VM_NODE_SELECTOR}    ${IMAGE_NAME}    node_name=${NODE_NAME}
    And VM should be running    ${VM_NODE_SELECTOR}
    Then VM Node Selector Check Should Report VM    ${VM_NODE_SELECTOR}

*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMAGE_NAME}           image-${suffix}
    Set Suite Variable    ${VM_NODE_SELECTOR}     vm-node-selector-${suffix}
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
    Run Keyword And Ignore Error    VM is deleted    ${VM_NODE_SELECTOR}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
