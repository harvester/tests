*** Settings ***
Documentation    Volume API Negative Test Cases (CRUD on missing / invalid resources)
...    Port of harvester/tests apis/test_volumes.py TestVolumesNegative.
...    Covers get/delete of a non-existent volume and creation without size/name.
Test Tags        storage    volume    negative    pr-baseline

Resource    ../../keywords/variables.resource
Resource    ../../keywords/common.resource
Resource    ../../keywords/volume.resource

Suite Setup       Set up test environment
Test Teardown     Common Test Teardown


*** Test Cases ***
Get Non-Existent Volume Returns Not Found
    [Tags]    p0
    [Documentation]    Getting a volume that does not exist must return 404 NotFound
    ${vol_name}=    Generate Unique Name    vol-missing
    ${result}=    Try To Get Volume    ${vol_name}
    Operation Should Be Not Found    ${result}

Delete Non-Existent Volume Returns Not Found
    [Tags]    p0
    [Documentation]    Deleting a volume that does not exist must return 404 NotFound
    ${vol_name}=    Generate Unique Name    vol-missing
    ${result}=    Try To Delete Volume    ${vol_name}
    Operation Should Be Not Found    ${result}

Reject Volume Creation Without Size
    [Tags]    p0
    [Documentation]    A volume requested with a zero/empty size must be rejected (422)
    ${vol_name}=    Generate Unique Name    vol-nosize
    ${result}=    Try To Create Volume    ${vol_name}    0
    Operation Should Be Rejected    ${result}    must be greater than zero
    Volume Should Not Exist    ${vol_name}

Reject Volume Creation Without Name
    [Tags]    p0    known-issue
    [Documentation]    Creating a volume with an empty name should be rejected (422).
    ...    Behaviour changed in v1.4.0; upstream gates this with skip_if_version.
    ...    Tracking: https://github.com/harvester/harvester/issues/7030
    Skip    Version-gated (>= v1.4.0 breaking change, harvester#7030)
