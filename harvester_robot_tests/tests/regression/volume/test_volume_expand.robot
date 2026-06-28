*** Settings ***
Documentation    Volume (PVC) Expansion Test Cases
Test Tags        storage    volume    expand    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${VOL_TAG}        volume-expand
# Dynamic Variables
${VOL_NAME}       ${EMPTY}


*** Test Cases ***
Create Volume And Verify Bound
    [Tags]    p0
    [Documentation]    Create a 10Gi volume to be used as the expansion target
    When Create 10Gi Volume    ${VOL_NAME}
    And Wait Until Volume Is Active    ${VOL_NAME}
    Then Volume Size Is 10Gi    ${VOL_NAME}

Expand Volume Size
    [Tags]    p0
    [Documentation]    Expand an unattached volume from 10Gi to 20Gi
    Given Volume Size Is 10Gi    ${VOL_NAME}
    When Update Volume Size to 20Gi    ${VOL_NAME}
    And Wait Until Volume Is Active    ${VOL_NAME}
    Then Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    Volume Size Is 20Gi    ${VOL_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    ${VOL_TAG}
    Set Suite Variable    ${VOL_NAME}    vol-exp-${suffix}
    Set up test environment

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named volume.
    # Keep the failure state for debugging by cleaning up only when all tests pass.
    Run Keyword If All Tests Passed    Delete Suite Volumes
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Volumes
    Run Keyword And Ignore Error    Delete Volume    ${VOL_NAME}
