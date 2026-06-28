*** Settings ***
Documentation    VM Lifecycle Operations Test Cases
...    Port of harvester/tests test_3_vm_functions.py TestVMOperations
...    (pause/unpause/stop/start/restart/delete).
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
Pause And Unpause VM
    [Tags]    p0    smoke
    [Documentation]    Pause a running VM then unpause it; it must return to running
    VM is paused    ${VM_NAME}
    VM should be paused    ${VM_NAME}
    VM is unpaused    ${VM_NAME}
    VM should be running    ${VM_NAME}

Stop And Start VM
    [Tags]    p0    smoke
    [Documentation]    Stop then start the VM
    VM is stopped    ${VM_NAME}
    VM should be stopped    ${VM_NAME}
    VM is started    ${VM_NAME}
    VM should be running    ${VM_NAME}

Restart VM
    [Tags]    p0    smoke
    [Documentation]    Restart the VM; it must come back to running
    VM is restarted    ${VM_NAME}
    VM should be running    ${VM_NAME}

Delete VM
    [Tags]    p0
    [Documentation]    Delete the VM and verify it is removed
    VM is deleted    ${VM_NAME}
    VM should be deleted    ${VM_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}    img-${suffix}
    Set Suite Variable    ${VM_NAME}     vm-${suffix}
    Set up test environment
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    VM is created    ${VM_NAME}    ${IMG_NAME}
    VM should be running    ${VM_NAME}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
