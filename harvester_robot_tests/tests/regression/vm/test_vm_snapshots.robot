*** Settings ***
Documentation    VM Test Cases
Test Tags        regression    virtualmachines

Resource         ../../../keywords/variables.resource
Resource         ../../../keywords/common.resource
Resource         ../../../keywords/image.resource
Resource         ../../../keywords/virtualmachine.resource
Resource         ../../../keywords/snapshot.resource


Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables (set by Local Suite Setup)
${IMAGE_NAME}       ${EMPTY}
${VM_NAME}          ${EMPTY}
${SNAPSHOT_NAME}    ${EMPTY}


*** Test Cases ***
Test Basic VM Snapshot
    [Tags]    coretest    p0    snapshot
    [Documentation]    Test basic VM snapshot creation

    Given Image is available for VM creation    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}
    When VM is created                 ${VM_NAME}        ${IMAGE_NAME}
    Then VM should be running          ${VM_NAME}
    When Snapshot is created           ${VM_NAME}        ${SNAPSHOT_NAME}
    Then Snapshot should be ready      ${SNAPSHOT_NAME}
    When Snapshot is deleted           ${SNAPSHOT_NAME}
    Then Snapshot should be deleted    ${SNAPSHOT_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMAGE_NAME}       image-0-${suffix}
    Set Suite Variable    ${VM_NAME}          vm-0-${suffix}
    Set Suite Variable    ${SNAPSHOT_NAME}    snap-0-${suffix}
    Set up test environment

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources (never a global
    # label sweep, which would remove resources owned by sibling suites under pabot).
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    # Defensive: the snapshot is deleted by the test itself on the happy path.
    Run Keyword And Ignore Error    Snapshot is deleted    ${SNAPSHOT_NAME}
    Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
    # Wait for the VM (and its volumes) to be gone so the image is no longer in use.
    Run Keyword And Ignore Error    VM should be deleted    ${VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
