*** Settings ***
Documentation    Volume Negative Creation Test Cases (invalid specifications)
...    Port of harvester/tests test_create_volume_invalid_specifications.
...    Each invalid size must be rejected by the API (400/422) with a matching
...    error message, and no volume resource should be left behind.
Test Tags        storage    volume    negative    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/volume.resource

Suite Setup       Set up test environment
Test Teardown     Invalid Volume Test Teardown


*** Variables ***
# Dynamic Variable: name of the volume attempted in the current test, used so the
# teardown can defensively remove it if the creation unexpectedly succeeded.
${CURRENT_INVALID_VOL}    ${EMPTY}


*** Test Cases ***
Reject Volume With Zero Size
    [Tags]    p1
    [Documentation]    A 0Gi volume request must be rejected as "must be greater than zero"
    Volume Creation Should Fail    0Gi    must be greater than zero

Reject Volume With Negative Size
    [Tags]    p1
    [Documentation]    A negative size request must be rejected as "must be greater than zero"
    Volume Creation Should Fail    -5Gi    must be greater than zero

Reject Volume With Non-Numeric Size
    [Tags]    p1
    [Documentation]    A non-quantity size string must be rejected as a quantity parse error
    Volume Creation Should Fail    invalid_size    quantities must match

Reject Volume Exceeding Cluster Capacity
    [Tags]    p1    known-issue
    [Documentation]    An oversized request should be rejected but currently is not.
    ...    Tracking: https://github.com/harvester/harvester/issues/9268
    Skip    Known issue harvester#9268: oversized volume request is not rejected


*** Keywords ***
Volume Creation Should Fail
    [Arguments]    ${size}    ${expected_message}
    [Documentation]    Attempt to create a volume with an invalid size and assert the API
    ...    rejects it (400/422) with the expected message, leaving no volume behind.
    ${vol_name}=    Generate Unique Name    vol-invalid
    Set Test Variable    ${CURRENT_INVALID_VOL}    ${vol_name}
    ${result}=    Try To Create Volume    ${vol_name}    ${size}
    Operation Should Be Rejected    ${result}    ${expected_message}
    Volume Should Not Exist    ${vol_name}

Invalid Volume Test Teardown
    Run Keyword If Test Failed    Log Variables
    # Defensive: if a volume was unexpectedly created, remove it. Parallel-safe -
    # only ever touches this test's own generated volume name.
    Run Keyword If    '${CURRENT_INVALID_VOL}' != '${EMPTY}'
    ...    Run Keyword And Ignore Error    Delete Volume    ${CURRENT_INVALID_VOL}
