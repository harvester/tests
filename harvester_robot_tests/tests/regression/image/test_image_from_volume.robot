*** Settings ***
Documentation    Volume-Based VirtualMachineImage Lifecycle Test Cases
Test Tags        image

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${VOL_NAME}    ${EMPTY}
${IMG_NAME}    ${EMPTY}


*** Test Cases ***
Create Image From Volume
    [Tags]    p0    pr-baseline
    [Documentation]    Create an image from a volume and verify its status and size
    Given A 1Gi Volume is Created    ${VOL_NAME}
    When Export Volume To Image    ${VOL_NAME}    ${IMG_NAME}
    Then Wait Until Image State Is Active    ${IMG_NAME}
    And Image Size Is 1Gi    ${IMG_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${VOL_NAME}    vol-${suffix}
    Set Suite Variable    ${IMG_NAME}    export-${VOL_NAME}
    Set up test environment

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    Run Keyword If All Tests Passed    Run Keywords
    ...   Run Keyword And Ignore Error    Delete volume    ${VOL_NAME}    AND
    ...   Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
