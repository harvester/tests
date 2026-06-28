*** Settings ***
Documentation    Image-Backed Volume Resize Test Cases
...    Port of harvester/tests test_volume_resize_operations.
...    An image-backed volume must survive multiple sequential expansions and
...    remain Bound after each one.
Test Tags        storage    volume    resize    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${IMG_NAME}       ${EMPTY}
${VOL_NAME}       ${EMPTY}
# Base size (GiB int) of the image-backed volume, captured after creation.
${BASE_GI}        ${EMPTY}


*** Test Cases ***
Create Image-Backed Volume And Verify Bound
    [Tags]    p0
    [Documentation]    Provision a volume from a VM image and capture its base size
    When Create Volume From Image    ${VOL_NAME}    ${IMG_NAME}
    And Wait Until Volume Is Active    ${VOL_NAME}
    Then Capture Base Volume Size    ${VOL_NAME}

Resize Image-Backed Volume Multiple Times
    [Tags]    p0    sanity
    [Documentation]    Expand the volume twice (base+5Gi, then base+10Gi); it must
    ...    reflect each new size and stay Bound throughout.
    Given Volume Is Present    ${VOL_NAME}
    ${first}=     Evaluate    ${BASE_GI} + 5
    ${second}=    Evaluate    ${BASE_GI} + 10
    When Expand Volume And Verify    ${VOL_NAME}    ${first}
    And Expand Volume And Verify    ${VOL_NAME}    ${second}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}    img-${suffix}
    Set Suite Variable    ${VOL_NAME}    vol-${suffix}
    Set up test environment
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}

Capture Base Volume Size
    [Arguments]    ${vol_name}
    [Documentation]    Read the bound volume's size (e.g. "10Gi") and store the GiB int
    ${size}=    Get Volume Size    ${vol_name}
    ${base_gi}=    Evaluate    int("${size}".rstrip("GiB"))
    Set Suite Variable    ${BASE_GI}    ${base_gi}
    Log    Image-backed volume base size is ${base_gi}Gi

Expand Volume And Verify
    [Arguments]    ${vol_name}    ${new_gi}
    [Documentation]    Expand to ${new_gi}Gi and confirm the size sticks and stays Bound
    Update Volume Size to ${new_gi}Gi    ${vol_name}
    Wait Until Volume Is Active    ${vol_name}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Volume Size Is ${new_gi}Gi    ${vol_name}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    Delete Volume    ${VOL_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
