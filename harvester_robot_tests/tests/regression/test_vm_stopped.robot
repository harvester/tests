*** Settings ***
Documentation    Create Stopped VM Test Cases
...    Port of harvester/tests test_create_stopped_vm.
...    A VM created with runStrategy=Halted must not boot, and must start on demand.
Test Tags        virtualmachines    pr-baseline

Resource    ../../keywords/variables.resource
Resource    ../../keywords/common.resource
Resource    ../../keywords/image.resource
Resource    ../../keywords/virtualmachine.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${IMG_NAME}    ${EMPTY}
${VM_NAME}     ${EMPTY}


*** Test Cases ***
Create Stopped VM Stays Stopped
    [Tags]    p0    sanity
    [Documentation]    A VM created with runStrategy=Halted must not boot
    Stopped VM is created    ${VM_NAME}    ${IMG_NAME}
    VM should be stopped    ${VM_NAME}

Start Stopped VM
    [Tags]    p0
    [Documentation]    Starting the stopped VM brings it to running
    VM is started    ${VM_NAME}
    VM should be running    ${VM_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}    img-${suffix}
    Set Suite Variable    ${VM_NAME}     vm-${suffix}
    Set up test environment
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
