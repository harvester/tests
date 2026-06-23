*** Settings ***
Documentation    VirtualMachineImage Valid Checksum Test Case
Test Tags        image    checksum    pr-baseline

Resource    ../../keywords/variables.resource
Resource    ../../keywords/common.resource
Resource    ../../keywords/image.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${IMAGE_TAG}            image-cksum
# A known-good SHA512 for ${OPENSUSE_IMAGE_URL}; leave empty to skip this test
${IMAGE_CHECKSUM}       %{IMAGE_CHECKSUM=}
# Dynamic Variables
${IMG_CHECKSUM_NAME}    ${EMPTY}


*** Test Cases ***
Create Image With Valid Checksum
    [Tags]    p1
    [Documentation]    Create an image with a correct SHA512 checksum; runs only when IMAGE_CHECKSUM is set
    Skip If    '${IMAGE_CHECKSUM}' == '${EMPTY}'    IMAGE_CHECKSUM not provided
    When Create image from url with name    ${IMG_CHECKSUM_NAME}    ${OPENSUSE_IMAGE_URL}    checksum=${IMAGE_CHECKSUM}
    And Wait for image downloaded by name    ${IMG_CHECKSUM_NAME}
    Then Image State Is Active    ${IMG_CHECKSUM_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    ${IMAGE_TAG}
    Set Suite Variable    ${IMG_CHECKSUM_NAME}    img-cksum-${suffix}
    Set up test environment

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named image.
    # Keep the failure state for debugging; clean up only when all tests pass.
    Run Keyword If All Tests Passed    Delete Suite Images
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Images
    Run Keyword And Ignore Error    Delete image by name    ${IMG_CHECKSUM_NAME}
