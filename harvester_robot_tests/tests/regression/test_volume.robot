*** Settings ***
Documentation    Volume (PVC) Basic Lifecycle Test Cases
Test Tags        storage    volume    pr-baseline

Resource    ../../keywords/variables.resource
Resource    ../../keywords/common.resource
Resource    ../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${VOL_TAG}              volume
# Dynamic Variables
${VOL_NAME}             ${EMPTY}
${VOL_REPLICA_NAME}     ${EMPTY}


*** Test Cases ***
Create Volume And Verify Bound
    [Tags]    p0
    [Documentation]    Create a 10Gi volume with the default storage class and verify it becomes Bound
    When Create 10Gi Volume    ${VOL_NAME}
    And Wait Until Volume Is Active    ${VOL_NAME}
    Then Volume Size Is 10Gi    ${VOL_NAME}

Create Volume With Custom Replicas
    [Tags]    p1
    [Documentation]    Create a volume requesting a single replica and verify it becomes Bound
    When Create Volume    ${VOL_REPLICA_NAME}    size=5Gi    replicas=1
    And Wait Until Volume Is Active    ${VOL_REPLICA_NAME}
    Then Volume Size Is 5Gi    ${VOL_REPLICA_NAME}

List Volumes
    [Tags]    p1
    [Documentation]    Listed volumes should contain the volumes created in this suite
    Given Volume Is Present    ${VOL_NAME}
    And Volume Is Present    ${VOL_REPLICA_NAME}
    Then Volume Should Be Listed    ${VOL_NAME}
    And Volume Should Be Listed    ${VOL_REPLICA_NAME}

Delete Volume
    [Tags]    p0
    [Documentation]    Delete a volume and verify the resource is reclaimed
    Given Volume Is Present    ${VOL_REPLICA_NAME}
    When Delete Volume    ${VOL_REPLICA_NAME}
    Then Wait Until Volume Is Deleted    ${VOL_REPLICA_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    ${VOL_TAG}
    Set Suite Variable    ${VOL_NAME}             vol-${suffix}
    Set Suite Variable    ${VOL_REPLICA_NAME}     vol-r-${suffix}
    Set up test environment

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named volumes (never a global
    # label sweep, which would remove volumes owned by sibling suites under pabot).
    # Keep the failure state for debugging by cleaning up only when all tests pass.
    Run Keyword If All Tests Passed    Delete Suite Volumes
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Volumes
    Run Keyword And Ignore Error    Delete Volume    ${VOL_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${VOL_REPLICA_NAME}
