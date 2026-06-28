*** Settings ***
Documentation    Image API Negative Test Cases (CRUD on missing / invalid resources)
...    Port of harvester/tests apis/test_images.py TestImagesNegative.
...    Covers get/delete of a non-existent image and creation with empty data/url.
Test Tags        image    negative    pr-baseline

Resource    ../../keywords/variables.resource
Resource    ../../keywords/common.resource
Resource    ../../keywords/image.resource

Suite Setup       Set up test environment
Test Teardown     Invalid Image Test Teardown


*** Variables ***
# Name of the image attempted in the current test, so the teardown can remove it
# if a creation that should have failed unexpectedly succeeded.
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


*** Keywords ***
Invalid Image Test Teardown
    Run Keyword If Test Failed    Log Variables
    # Defensive: if an image was unexpectedly created, remove it. Parallel-safe -
    # only ever touches this test's own generated image name.
    Run Keyword If    '${CURRENT_IMG}' != '${EMPTY}'
    ...    Run Keyword And Ignore Error    Delete image by name    ${CURRENT_IMG}
