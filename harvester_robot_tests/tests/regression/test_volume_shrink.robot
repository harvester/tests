*** Settings ***
Documentation    Volume Shrink Rejection Test Cases
...    Port of harvester/tests test_volume_shrink_not_allowed.
...    Shrinking a PVC must be rejected by the API and leave the volume unchanged.
Test Tags        storage    volume    negative    pr-baseline

Resource    ../../keywords/variables.resource
Resource    ../../keywords/common.resource
Resource    ../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${VOL_NAME}    ${EMPTY}


*** Test Cases ***
Create Volume And Verify Bound
    [Tags]    p0
    [Documentation]    Create a 10Gi volume to be used as the shrink target
    When Create 10Gi Volume    ${VOL_NAME}
    And Wait Until Volume Is Active    ${VOL_NAME}
    Then Volume Size Is 10Gi    ${VOL_NAME}

Reject Shrinking Volume
    [Tags]    p2
    [Documentation]    Attempting to shrink 10Gi -> 5Gi must be rejected, and the
    ...    volume must keep its original size and stay Bound.
    Volume Size Is 10Gi    ${VOL_NAME}
    ${result}=    Try To Resize Volume    ${VOL_NAME}    5Gi
    Operation Should Be Rejected    ${result}    forbidden    not allowed    not supported    less than    cannot
    Volume Size Is 10Gi    ${VOL_NAME}
    Volume Phase Is Bound    ${VOL_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${VOL_NAME}    vol-shrink-${suffix}
    Set up test environment

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named volume.
    Run Keyword If All Tests Passed    Delete Suite Volumes
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Volumes
    Run Keyword And Ignore Error    Delete Volume    ${VOL_NAME}
