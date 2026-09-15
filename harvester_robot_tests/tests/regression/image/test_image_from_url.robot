*** Settings ***
Documentation    URL-Based VirtualMachineImage Lifecycle Test Cases
Test Tags        image

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# A known-good SHA512 for ${OPENSUSE_IMAGE_URL}; leave empty to skip that test
${IMAGE_CHECKSUM}       %{IMAGE_CHECKSUM=}
# Dynamic Variables
${IMG_NAME}             ${EMPTY}
${IMG_CHECKSUM_NAME}    ${EMPTY}
${VOL_NAME}             ${EMPTY}


*** Test Cases ***
Create Image From URL And Verify Active
    [Tags]    p0    pr-baseline
    [Documentation]    Create an image from a URL, wait until downloaded and Active, verify size
    When Create image from url with name    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    And Wait for image downloaded by name    ${IMG_NAME}
    Then Image State Is Active    ${IMG_NAME}
    And Image Size Is Greater Than Zero    ${IMG_NAME}

List Images And Image Exists
    [Tags]    p1    pr-baseline
    [Documentation]    The created image should be listed and reported as existing
    Given Image Should Exist    ${IMG_NAME}
    Then Image Should Be Listed    ${IMG_NAME}

Get Single Image
    [Tags]    p1    pr-baseline
    [Documentation]    Getting the image by name returns it with the matching name
    Get Image By Name    ${IMG_NAME}

Update Image Metadata
    [Tags]    p0    pr-baseline
    [Documentation]    Update labels and annotations and verify they persist
    ${labels}=    Create Dictionary    test-label=42
    ${annotations}=    Create Dictionary    test-annotation=dummy    field.cattle.io/description=test description
    ${metadata}=    Create Dictionary    labels=${labels}    annotations=${annotations}
    Update Image Metadata    ${IMG_NAME}    ${metadata}
    Image Label Should Be    ${IMG_NAME}    test-label    42
    Image Annotation Should Be    ${IMG_NAME}    test-annotation    dummy

Create Image With Valid Checksum
    [Tags]    p1    checksum    pr-baseline
    [Documentation]    Create an image with a correct SHA512 checksum; runs only when
    ...    IMAGE_CHECKSUM is set. Uses its own image, independent of the main one.
    Skip If    '${IMAGE_CHECKSUM}' == '${EMPTY}'    IMAGE_CHECKSUM not provided
    When Create image from url with name    ${IMG_CHECKSUM_NAME}    ${OPENSUSE_IMAGE_URL}    checksum=${IMAGE_CHECKSUM}
    And Wait for image downloaded by name    ${IMG_CHECKSUM_NAME}
    Then Image State Is Active    ${IMG_CHECKSUM_NAME}

Delete Image
    [Tags]    p0    pr-baseline
    [Documentation]    Delete an image and verify it is removed
    Given Image Should Exist    ${IMG_NAME}
    When Delete image by name    ${IMG_NAME}
    Then Wait for image deleted by name    ${IMG_NAME}

Recreate Image With Same Name
    # TODO: Implement skip_if_version
    # @pytest.mark.skip_if_version(">= v1.2.0", "< v1.4.0",
    #         reason="https://github.com/harvester/harvester/issues/4293 fix after `v1.4.0`")
    [Tags]    p0
    [Documentation]    Delete an image via URL, remove it and create a new one with the same name
    Given Image Should Not Exist    ${IMG_NAME}
    When Create image from url with name    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    And Wait for image downloaded by name    ${IMG_NAME}
    Then Image State Is Active    ${IMG_NAME}
    And Image Size Is Greater Than Zero    ${IMG_NAME}

Edit Image In Use
    [Tags]    p0
    ${labels}=    Create Dictionary
    ...    test-label=foo
    ${annotations}=    Create Dictionary
    ...    test-annotation=foo
    ...    field.cattle.io/description=foo bar
    ${metadata}=    Create Dictionary
    ...    labels=${labels}
    ...    annotations=${annotations}

    Given Image Should Exist    ${IMG_NAME}
    And Create Volume From Image    ${VOL_NAME}    ${IMG_NAME}
    And Wait Until Volume Is Active    ${VOL_NAME}
    When Update Image Metadata    ${IMG_NAME}    ${metadata}
    Then Image Label Should Be    ${IMG_NAME}    test-label    foo
    And Image Annotation Should Be    ${IMG_NAME}    test-annotation    foo
    And Image Annotation Should Be    ${IMG_NAME}    field.cattle.io/description    foo bar


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}             img-${suffix}
    Set Suite Variable    ${IMG_CHECKSUM_NAME}    img-cksum-${suffix}
    Set Suite Variable    ${VOL_NAME}             vol-${suffix}
    Set up test environment

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    Run Keyword If All Tests Passed    Run Keywords
    ...   Run Keyword And Ignore Error    Delete volume    ${VOL_NAME}    AND
    ...   Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}    AND
    ...   Run Keyword And Ignore Error    Delete image by name    ${IMG_CHECKSUM_NAME}
