*** Settings ***
Documentation    VM API Negative Test Cases
...    Port of harvester/tests apis/test_vms.py TestVMNegative.
...    Getting/deleting a non-existent VM must return 404 NotFound.
Test Tags        virtualmachines    negative    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/virtualmachine.resource

Suite Setup       Set up test environment
Test Teardown     Common Test Teardown


*** Test Cases ***
Get Non-Existent VM Returns Not Found
    [Tags]    p0
    [Documentation]    Getting a VM that does not exist must return 404 NotFound
    ${vm}=    Generate Unique Name    vm-missing
    ${result}=    Try To Get VM    ${vm}
    Operation Should Be Not Found    ${result}

Delete Non-Existent VM Returns Not Found
    [Tags]    p0
    [Documentation]    Deleting a VM that does not exist must return 404 NotFound
    ${vm}=    Generate Unique Name    vm-missing
    ${result}=    Try To Delete VM    ${vm}
    Operation Should Be Not Found    ${result}
