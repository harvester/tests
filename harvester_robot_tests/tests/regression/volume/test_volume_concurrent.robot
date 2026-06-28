*** Settings ***
Documentation    Concurrent Volume Creation Test Cases
...    Port of harvester/tests test_concurrent_volume_creation.
...    Creating several volumes in parallel must all succeed and bind, validating
...    API thread-safety and Longhorn concurrent provisioning.
Test Tags        storage    volume    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${CONCURRENT_COUNT}    3
# Dynamic Variables
@{VOL_NAMES}           @{EMPTY}


*** Test Cases ***
Create Volumes Concurrently And Verify Bound
    [Tags]    p2
    [Documentation]    Create ${CONCURRENT_COUNT} volumes in parallel; all must
    ...    succeed, reach Bound, then delete cleanly in parallel.
    ${results}=    Create Volumes Concurrently    ${VOL_NAMES}
    All Volume Operations Should Succeed    ${results}
    Length Should Be    ${results}    ${CONCURRENT_COUNT}
    FOR    ${vol_name}    IN    @{VOL_NAMES}
        Volume Phase Is Bound    ${vol_name}
    END
    ${cleanup}=    Delete Volumes Concurrently    ${VOL_NAMES}
    All Volume Operations Should Succeed    ${cleanup}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    @{names}=    Create List
    FOR    ${i}    IN RANGE    ${CONCURRENT_COUNT}
        Append To List    ${names}    vol-conc-${i}-${suffix}
    END
    Set Suite Variable    @{VOL_NAMES}    @{names}
    Set up test environment

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named volumes.
    Run Keyword If All Tests Passed    Delete Suite Volumes
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Volumes
    FOR    ${vol_name}    IN    @{VOL_NAMES}
        Run Keyword And Ignore Error    Delete Volume    ${vol_name}
    END
