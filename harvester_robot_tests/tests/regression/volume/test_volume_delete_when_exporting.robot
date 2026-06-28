*** Settings ***
Documentation    Delete Volume While Exporting Test Case
...    Port of harvester/tests test_delete_volume_when_exporting.
...    A volume that is being exported to an image must not be deletable; the
...    admission webhook should reject the delete and leave the volume intact.
Test Tags        storage    volume    negative    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${VOL_NAME}           ${EMPTY}
${EXPORT_IMG_NAME}    ${EMPTY}


*** Test Cases ***
Reject Deleting Volume While Exporting
    [Tags]    p1
    [Documentation]    Start an export of the volume, then attempt to delete it; the
    ...    delete must be rejected (4xx) and the volume must still be present.
    Volume Is Present    ${VOL_NAME}
    Export Volume To Image    ${VOL_NAME}    ${EXPORT_IMG_NAME}
    ${result}=    Try To Delete Volume    ${VOL_NAME}
    Operation Should Be Rejected    ${result}
    Volume Is Present    ${VOL_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${VOL_NAME}           vol-export-${suffix}
    Set Suite Variable    ${EXPORT_IMG_NAME}    img-export-${suffix}
    Set up test environment
    Create Volume    ${VOL_NAME}    5Gi
    Wait Until Volume Is Active    ${VOL_NAME}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    # Remove the export image first so the source volume is no longer in use.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    Delete image by name    ${EXPORT_IMG_NAME}
    Run Keyword And Ignore Error    Wait for image deleted by name    ${EXPORT_IMG_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${VOL_NAME}
