*** Settings ***
Documentation    VM Test Cases
Test Tags        regression    virtualmachines

Resource         ../../keywords/variables.resource
Resource         ../../keywords/common.resource
Resource         ../../keywords/virtualmachine.resource

Test Setup       Set up test environment
Test Teardown    Cleanup test resources

*** Test Cases ***
Test VM Basic Lifecycle
    [Tags]    coretest    p0
    [Documentation]    Test basic VM creation, start, stop, delete operations

    # Generate unique names for vm & image using timestamp
    ${timestamp}=    Get Current Date    result_format=%Y%m%d%H%M%S%f
    ${image_name}=    Set Variable    image-0-${timestamp}
    ${vm_name}=    Set Variable    vm-0-${timestamp}

    Given Image is available for VM creation   ${image_name}    ${OPENSUSE_IMAGE_URL}
    When VM is created    ${vm_name}    cpu=2    memory=4Gi    image_id=${image_name}
    Then VM should be running    ${vm_name}
    And VM should have IP addresses    ${vm_name}    ${DEFAULT_NAMESPACE}
    When VM is stopped    ${vm_name}
    Then VM should be stopped    ${vm_name}
    When VM is started    ${vm_name}
    Then VM should be running    ${vm_name}
    When VM is deleted    ${vm_name}
    Then VM should be deleted    ${vm_name}
