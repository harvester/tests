*** Settings ***
Documentation    Volume (PVC) Snapshot and Restore Test Cases
Test Tags        storage    volume    snapshot

Resource    ../../keywords/variables.resource
Resource    ../../keywords/common.resource
Resource    ../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${VOL_TAG}              volume-snapshot
# Dynamic Variables
${SRC_VOL_NAME}         ${EMPTY}
${SNAPSHOT_NAME}        ${EMPTY}
${RESTORED_VOL_NAME}    ${EMPTY}


*** Test Cases ***
Create Source Volume
    [Tags]    p1
    [Documentation]    Create a 10Gi source volume to snapshot from
    When Create 10Gi Volume    ${SRC_VOL_NAME}
    And Wait Until Volume Is Active    ${SRC_VOL_NAME}
    Then Volume Size Is 10Gi    ${SRC_VOL_NAME}

Create Volume Snapshot
    [Tags]    p1
    [Documentation]    Create a snapshot of a Bound volume and wait until it is ready to use
    Given Volume Is Present    ${SRC_VOL_NAME}
    When Create Volume Snapshot    ${SRC_VOL_NAME}    ${SNAPSHOT_NAME}
    Then Wait Until Snapshot Is Ready    ${SNAPSHOT_NAME}

Restore Volume From Snapshot
    [Tags]    p1
    [Documentation]    Restore a new volume from the snapshot and verify it is Bound with the same size
    Given Wait Until Snapshot Is Ready    ${SNAPSHOT_NAME}
    When Restore Volume From Snapshot    ${SRC_VOL_NAME}    ${SNAPSHOT_NAME}    ${RESTORED_VOL_NAME}
    And Wait Until Volume Is Active    ${RESTORED_VOL_NAME}
    Then Volume Size Is 10Gi    ${RESTORED_VOL_NAME}

Delete Volume Snapshot
    [Tags]    p1
    [Documentation]    Delete the snapshot created earlier
    When Delete Volume Snapshot    ${SRC_VOL_NAME}    ${SNAPSHOT_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    ${VOL_TAG}
    Set Suite Variable    ${SRC_VOL_NAME}         vol-snap-${suffix}
    Set Suite Variable    ${SNAPSHOT_NAME}        snap-${suffix}
    Set Suite Variable    ${RESTORED_VOL_NAME}    vol-restored-${suffix}
    Set up test environment

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    # Keep the failure state for debugging by cleaning up only when all tests pass.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    Delete Volume Snapshot    ${SRC_VOL_NAME}    ${SNAPSHOT_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${RESTORED_VOL_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${SRC_VOL_NAME}
