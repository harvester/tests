*** Settings ***
Documentation    VM Test Cases
Test Tags        regression    virtualmachines

Resource         ../../keywords/variables.resource
Resource         ../../keywords/common.resource
Resource         ../../keywords/image.resource
Resource         ../../keywords/virtualmachine.resource
Resource         ../../keywords/snapshot.resource


Suite Setup       Set up test environment
Test Teardown    Cleanup test resources
Suite Teardown   Common Suite Teardown


*** Test Cases ***
Test Basic VM Snapshot
    [Tags]    coretest    p0    snapshot
    [Documentation]    Test basic VM snapshot creation

    # Generate unique name for vm, image and snapshot
    ${suffix}=    Generate Unique Name
    ${image_name}=    Set Variable    image-0-${suffix}
    ${vm_name}=    Set Variable    vm-0-${suffix}
    ${snapshot_name}=    Set Variable    snap-0-${suffix}

    Given Image is available for VM creation    ${image_name}    ${OPENSUSE_IMAGE_URL}
    When VM is created                 ${vm_name}        ${image_name}
    Then VM should be running          ${vm_name}
    When Snapshot is created           ${vm_name}        ${snapshot_name}
    Then Snapshot should be ready      ${snapshot_name}
    When Snapshot is deleted           ${snapshot_name}
    Then Snapshot should be deleted    ${snapshot_name}
