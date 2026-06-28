*** Settings ***
Documentation    VirtualMachineImage Invalid URL Test Case
Test Tags        image    negative    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${IMAGE_TAG}            image-badurl
${INVALID_IMAGE_URL}    https://invalid.example.invalid/nonexistent-image.qcow2
# Dynamic Variables
${IMG_BAD_URL_NAME}     ${EMPTY}


*** Test Cases ***
Create Image With Invalid URL
    [Tags]    p1
    [Documentation]    An unreachable URL must fail the import and never become Active
    When Create image from url with name    ${IMG_BAD_URL_NAME}    ${INVALID_IMAGE_URL}
    Then Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    Image State Is Failed    ${IMG_BAD_URL_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    ${IMAGE_TAG}
    Set Suite Variable    ${IMG_BAD_URL_NAME}    img-badurl-${suffix}
    Set up test environment

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named image.
    # Keep the failure state for debugging; clean up only when all tests pass.
    Run Keyword If All Tests Passed    Delete Suite Images
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Images
    Run Keyword And Ignore Error    Delete image by name    ${IMG_BAD_URL_NAME}
