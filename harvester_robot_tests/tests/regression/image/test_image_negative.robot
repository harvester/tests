*** Settings ***
Documentation    Image Negative Test Cases (missing / invalid resources, bad checksum/url)
...    Port of harvester/tests apis/test_images.py TestImagesNegative plus the
...    invalid-checksum and invalid-url import cases.
Test Tags        image    negative    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource

Suite Setup       Set up test environment
Test Teardown     Invalid Image Test Teardown


*** Variables ***
# Well-formed but wrong SHA512 (128 hex chars) to force a checksum mismatch
${INVALID_CHECKSUM}     00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
${INVALID_IMAGE_URL}    https://invalid.example.invalid/nonexistent-image.qcow2
# Name of the image attempted in the current test, so the teardown can remove it
# (a failed-import image, or a creation that should have failed but succeeded).
${CURRENT_IMG}    ${EMPTY}


*** Test Cases ***
Get Non-Existent Image Returns Not Found
    [Tags]    p0
    [Documentation]    Getting an image that does not exist must return 404 NotFound
    ${img}=    Generate Unique Name    img-missing
    ${result}=    Try To Get Image    ${img}
    Operation Should Be Not Found    ${result}

Delete Non-Existent Image Returns Not Found
    [Tags]    p0
    [Documentation]    Deleting an image that does not exist must return 404 NotFound
    ${img}=    Generate Unique Name    img-missing
    ${result}=    Try To Delete Image    ${img}
    Operation Should Be Not Found    ${result}

Reject Image Creation With Empty Data
    [Tags]    p0
    [Documentation]    Creating an image with empty sourceType/url must be rejected (4xx)
    ${img}=    Generate Unique Name    img-empty
    Set Test Variable    ${CURRENT_IMG}    ${img}
    ${result}=    Try To Create Image    ${img}    source_type=${EMPTY}
    Operation Should Be Rejected    ${result}

Reject Image Creation With Empty URL
    [Tags]    p0
    [Documentation]    Creating a download image with an empty url must be rejected (4xx)
    ${img}=    Generate Unique Name    img-emptyurl
    Set Test Variable    ${CURRENT_IMG}    ${img}
    ${result}=    Try To Create Image    ${img}    ${EMPTY}
    Operation Should Be Rejected    ${result}

Create Image With Invalid Checksum
    [Tags]    p1    checksum
    [Documentation]    A wrong checksum must fail verification and never become Active
    ${img}=    Generate Unique Name    img-badcksum
    Set Test Variable    ${CURRENT_IMG}    ${img}
    When Create image from url with name    ${img}    ${OPENSUSE_IMAGE_URL}    checksum=${INVALID_CHECKSUM}
    Then Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Image State Is Failed    ${img}

Create Image With Invalid URL
    [Tags]    p1
    [Documentation]    An unreachable URL must fail the import and never become Active
    ${img}=    Generate Unique Name    img-badurl
    Set Test Variable    ${CURRENT_IMG}    ${img}
    When Create image from url with name    ${img}    ${INVALID_IMAGE_URL}
    Then Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Image State Is Failed    ${img}


*** Keywords ***
Invalid Image Test Teardown
    Run Keyword If Test Failed    Log Variables
    # Defensive: if an image was unexpectedly created, remove it. Parallel-safe -
    # only ever touches this test's own generated image name.
    Run Keyword If    '${CURRENT_IMG}' != '${EMPTY}'
    ...    Run Keyword And Ignore Error    Delete image by name    ${CURRENT_IMG}
