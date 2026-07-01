*** Settings ***
Documentation    VirtualMachineImage Lifecycle Test Cases
Test Tags        image    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${IMAGE_TAG}            image
# A known-good SHA512 for ${OPENSUSE_IMAGE_URL}; leave empty to skip that test
${IMAGE_CHECKSUM}       %{IMAGE_CHECKSUM=}
# Dynamic Variables
${IMAGE_NAME}           ${EMPTY}
${IMG_CHECKSUM_NAME}    ${EMPTY}


*** Test Cases ***
Create Image From URL And Verify Active
    [Tags]    p0
    [Documentation]    Create an image from a URL, wait until downloaded and Active, verify size
    When Create image from url with name    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}
    And Wait for image downloaded by name    ${IMAGE_NAME}
    Then Image State Is Active    ${IMAGE_NAME}
    And Image Size Is Greater Than Zero    ${IMAGE_NAME}

List Images And Image Exists
    [Tags]    p1
    [Documentation]    The created image should be listed and reported as existing
    Given Image Should Exist    ${IMAGE_NAME}
    Then Image Should Be Listed    ${IMAGE_NAME}

Get Single Image
    [Tags]    p1
    [Documentation]    Getting the image by name returns it with the matching name
    Get Image By Name    ${IMAGE_NAME}

Update Image Metadata
    [Tags]    p0
    [Documentation]    Update labels and annotations and verify they persist
    ${labels}=    Create Dictionary    test-label=42
    ${annotations}=    Create Dictionary    test-annotation=dummy    field.cattle.io/description=test description
    ${metadata}=    Create Dictionary    labels=${labels}    annotations=${annotations}
    Update Image Metadata    ${IMAGE_NAME}    ${metadata}
    Image Label Should Be    ${IMAGE_NAME}    test-label    42
    Image Annotation Should Be    ${IMAGE_NAME}    test-annotation    dummy

Create Image With Valid Checksum
    [Tags]    p1    checksum
    [Documentation]    Create an image with a correct SHA512 checksum; runs only when
    ...    IMAGE_CHECKSUM is set. Uses its own image, independent of the main one.
    Skip If    '${IMAGE_CHECKSUM}' == '${EMPTY}'    IMAGE_CHECKSUM not provided
    When Create image from url with name    ${IMG_CHECKSUM_NAME}    ${OPENSUSE_IMAGE_URL}    checksum=${IMAGE_CHECKSUM}
    And Wait for image downloaded by name    ${IMG_CHECKSUM_NAME}
    Then Image State Is Active    ${IMG_CHECKSUM_NAME}

Delete Image
    [Tags]    p0
    [Documentation]    Delete an image and verify it is removed
    Given Image Should Exist    ${IMAGE_NAME}
    When Delete image by name    ${IMAGE_NAME}
    Then Wait for image deleted by name    ${IMAGE_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    ${IMAGE_TAG}
    Set Suite Variable    ${IMAGE_NAME}            img-${suffix}
    Set Suite Variable    ${IMG_CHECKSUM_NAME}     img-cksum-${suffix}
    Set up test environment

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named images.
    # Keep the failure state for debugging; clean up only when all tests pass.
    Run Keyword If All Tests Passed    Delete Suite Images
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Images
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMG_CHECKSUM_NAME}
