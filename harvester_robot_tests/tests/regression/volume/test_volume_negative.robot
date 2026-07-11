*** Settings ***
Documentation    Volume Negative Test Cases: missing resources, invalid specs,
...    shrink rejection, and delete-while-exporting rejection.
Test Tags        storage    volume    negative    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Invalid Volume Test Teardown


*** Variables ***
# Name of the volume attempted in the current invalid-spec test, so the teardown
# can defensively remove it if the creation unexpectedly succeeded.
${CURRENT_INVALID_VOL}    ${EMPTY}
# Dynamic Variables (resources created by the shrink / export tests)
${SHRINK_VOL}     ${EMPTY}
${EXPORT_VOL}     ${EMPTY}
${EXPORT_IMG}     ${EMPTY}


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

Reject Shrinking Volume
    [Tags]    p2
    [Documentation]    Create a 10Gi volume, then attempt to shrink it to 5Gi; the
    ...    resize must be rejected and the volume keep its size and stay Bound.
    Given Create 10Gi Volume    ${SHRINK_VOL}
    And Wait Until Volume Is Active    ${SHRINK_VOL}
    And Volume Size Is 10Gi    ${SHRINK_VOL}
    ${result}=    Try To Resize Volume    ${SHRINK_VOL}    5Gi
    Operation Should Be Rejected    ${result}    forbidden    not allowed    not supported    less than    cannot
    Volume Size Is 10Gi    ${SHRINK_VOL}
    Volume Phase Is Bound    ${SHRINK_VOL}

Reject Deleting Volume While Exporting
    [Tags]    p1
    [Documentation]    Start an export of the volume, then attempt to delete it; the
    ...    delete must be rejected (4xx) and the volume must still be present.
    Create Volume    ${EXPORT_VOL}    5Gi
    Wait Until Volume Is Active    ${EXPORT_VOL}
    Export Volume To Image    ${EXPORT_VOL}    ${EXPORT_IMG}
    # The delete-while-exporting guard is enforced via the webhook's informer
    # cache; wait until the controller has picked up the new image so the
    # protection is in effect before attempting the delete.
    Wait Until Image Export Has Started    ${EXPORT_IMG}
    ${result}=    Try To Delete Volume    ${EXPORT_VOL}
    Operation Should Be Rejected    ${result}
    Volume Is Present    ${EXPORT_VOL}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${SHRINK_VOL}    vol-shrink-${suffix}
    Set Suite Variable    ${EXPORT_VOL}    vol-export-${suffix}
    Set Suite Variable    ${EXPORT_IMG}    img-export-${suffix}
    Set up test environment

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
    # Defensive: if an invalid-spec volume was unexpectedly created, remove it.
    # Parallel-safe - only ever touches this test's own generated volume name.
    Run Keyword If    '${CURRENT_INVALID_VOL}' != '${EMPTY}'
    ...    Run Keyword And Ignore Error    Delete Volume    ${CURRENT_INVALID_VOL}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    # Remove the export image first so the source volume is no longer in use.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    Delete image by name    ${EXPORT_IMG}
    Run Keyword And Ignore Error    Wait for image deleted by name    ${EXPORT_IMG}
    Run Keyword And Ignore Error    Delete Volume    ${EXPORT_VOL}
    Run Keyword And Ignore Error    Delete Volume    ${SHRINK_VOL}
