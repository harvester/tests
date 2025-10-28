*** Settings ***
Documentation    VM Test Cases
Test Tags        regression    virtualmachines

Resource         ../../keywords/variables.resource
Resource         ../../keywords/common.resource
Resource         ../../keywords/image.resource
Resource         ../../keywords/virtualmachine.resource

Library          DateTime

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
    
    # GIVEN: Prepare the test environment with a VM image
    Given Create image from url with name    ${image_name}    ${OPENSUSE_IMAGE_URL}
    And Wait for image downloaded by name    ${image_name}
    
    # WHEN: Create and start a new VM
    When Create VM with name    ${vm_name}    cpu=2    memory=4Gi    image_id=${image_name}
    
    # THEN: Verify the VM starts successfully and gets IP address
    Then Wait for VM running by name    ${vm_name}
    And Wait for VM IP addresses by name    ${vm_name}    default
    
    # WHEN: Stop the VM
    When Stop VM by name    ${vm_name}
    
    # THEN: Verify the VM is in stopped state
    Then Wait for VM stopped by name    ${vm_name}
    
    # WHEN: Start the VM again
    When Start VM by name    ${vm_name}
    
    # THEN: Verify the VM is running again
    Then Wait for VM running by name    ${vm_name}
    
    # WHEN: Delete the VM
    When Delete VM by name    ${vm_name}
    
    # THEN: Verify the VM is removed from the system
    Then Wait for VM deleted by name    ${vm_name}
