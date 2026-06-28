*** Settings ***
Documentation    VM Test Cases
Test Tags        regression    virtualmachines    pr-baseline

Resource         ../../keywords/variables.resource
Resource         ../../keywords/common.resource
Resource         ../../keywords/image.resource
Resource         ../../keywords/virtualmachine.resource


Suite Setup       Local Suite Setup
Test Teardown     Common Test Teardown
Suite Teardown    Local Suite Teardown


*** Variables ***
# Dynamic Variables
${IMAGE_NAME}    ${EMPTY}
${VM_NAME}       ${EMPTY}


*** Test Cases ***
Test VM Basic Lifecycle
    [Tags]    coretest    p0
    [Documentation]    Test basic VM creation, start, stop, delete operations

    Given Image is available for VM creation   ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}
    When VM is created    ${VM_NAME}    ${IMAGE_NAME}
    Then VM should be running    ${VM_NAME}
    And VM should have IP addresses    ${VM_NAME}    ${DEFAULT_NAMESPACE}
    When VM is stopped    ${VM_NAME}
    Then VM should be stopped    ${VM_NAME}
    When VM is started    ${VM_NAME}
    Then VM should be running    ${VM_NAME}
    When VM is deleted    ${VM_NAME}
    Then VM should be deleted    ${VM_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMAGE_NAME}    image-0-${suffix}
    Set Suite Variable    ${VM_NAME}       vm-0-${suffix}
    Set up test environment

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources (never a global
    # label sweep, which would remove VMs/images owned by sibling suites under pabot).
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
