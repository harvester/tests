*** Settings ***
Documentation    Create Volume From VM Image Test Cases
...    Port of harvester/tests test_create_volume (source_type="VM Image").
...    A volume provisioned from an image must bind and carry the image's id.
Test Tags        storage    volume    pr-baseline

Resource    ../../keywords/variables.resource
Resource    ../../keywords/common.resource
Resource    ../../keywords/image.resource
Resource    ../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${IMG_NAME}    ${EMPTY}
${VOL_NAME}    ${EMPTY}


*** Test Cases ***
Create Volume From Image And Verify Bound
    [Tags]    p0    smoke
    [Documentation]    Provision a volume from a VM image; it must bind and be
    ...    annotated with the source image id.
    When Create Volume From Image    ${VOL_NAME}    ${IMG_NAME}
    And Wait Until Volume Is Active    ${VOL_NAME}
    Then Volume Image Id Should Be    ${VOL_NAME}    ${DEFAULT_NAMESPACE}/${IMG_NAME}

Delete Volume From Image
    [Tags]    p0
    [Documentation]    Delete the image-backed volume and verify it is reclaimed
    Given Volume Is Present    ${VOL_NAME}
    When Delete Volume    ${VOL_NAME}
    Then Wait Until Volume Is Deleted    ${VOL_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}    img-${suffix}
    Set Suite Variable    ${VOL_NAME}    vol-${suffix}
    Set up test environment
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    # Keep the failure state for debugging; clean up only when all tests pass.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    Delete Volume    ${VOL_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
