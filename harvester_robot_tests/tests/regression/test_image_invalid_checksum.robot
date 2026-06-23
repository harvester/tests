*** Settings ***
Documentation    VirtualMachineImage Invalid Checksum Test Case
Test Tags        image    checksum    negative    pr-baseline

Resource    ../../keywords/variables.resource
Resource    ../../keywords/common.resource
Resource    ../../keywords/image.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${IMAGE_TAG}            image-badcksum
# Well-formed but wrong SHA512 (128 hex chars) to force a checksum mismatch
${INVALID_CHECKSUM}     00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
# Dynamic Variables
${IMG_BAD_CKSUM_NAME}   ${EMPTY}


*** Test Cases ***
Create Image With Invalid Checksum
    [Tags]    p1
    [Documentation]    A wrong checksum must fail verification and never become Active
    When Create image from url with name    ${IMG_BAD_CKSUM_NAME}    ${OPENSUSE_IMAGE_URL}    checksum=${INVALID_CHECKSUM}
    Then Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    Image State Is Failed    ${IMG_BAD_CKSUM_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    ${IMAGE_TAG}
    Set Suite Variable    ${IMG_BAD_CKSUM_NAME}    img-badcksum-${suffix}
    Set up test environment

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named image.
    # Keep the failure state for debugging; clean up only when all tests pass.
    Run Keyword If All Tests Passed    Delete Suite Images
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Images
    Run Keyword And Ignore Error    Delete image by name    ${IMG_BAD_CKSUM_NAME}
