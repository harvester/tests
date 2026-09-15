*** Settings ***
Documentation    File-Based VirtualMachineImage Lifecycle Test Cases
Test Tags        image

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${IMG_NAME}              ${EMPTY}
${INVALID_IMAGE_FILE}    ${EMPTY}
${INVALID_IMAGE_PATH}    ${EMPTY}


*** Test Cases ***
Create Image From An Invalid File
    [Tags]    p0    negative
    [Documentation]    Upload an invalid, non-512-byte-aligned image file and verify rejection.
    When An Invalid Image File Is Prepared    ${INVALID_IMAGE_FILE}
    Then Upload Image File Should Be Rejected    ${IMG_NAME}    ${INVALID_IMAGE_PATH}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}    non512multiples-${suffix}.raw
    Set Suite Variable    ${INVALID_IMAGE_FILE}    ${IMG_NAME}
    Set Up Test Environment

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    Run Keyword If All Tests Passed    Run Keywords
    ...   Run Keyword And Ignore Error    Delete Image By Name    ${IMG_NAME}    AND
    ...   Run Keyword And Ignore Error    Remove File    ${INVALID_IMAGE_PATH}

An Invalid Image File Is Prepared
    [Arguments]    ${invalid_image_file}
    ${invalid_image_path}=    Create An Invalid Image File    ${invalid_image_file}
    Set Suite Variable    ${INVALID_IMAGE_PATH}    ${invalid_image_path}
