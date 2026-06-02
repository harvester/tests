*** Settings ***
Documentation    Image Keywords
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/image_keywords.py

*** Keywords ***
Create image from url with name
    [Arguments]    ${image_name}    ${image_url}    ${storage_class}=${EMPTY}    ${checksum}=
    [Documentation]    Create image from URL using provided name and optional storage class
    image_keywords.create image from url    ${image_name}    ${image_url}    storage_class=${storage_class}    checksum=${checksum}

Wait for image downloaded by name
    [Arguments]    ${image_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for image download to complete
    image_keywords.wait for image downloaded    ${image_name}    ${timeout}

Delete image by name
    [Arguments]    ${image_name}    ${namespace}=${DEFAULT_NAMESPACE}
    [Documentation]    Delete an image
    image_keywords.delete image    ${image_name}    ${namespace}

Get image status by name
    [Arguments]    ${image_name}    ${namespace}=${DEFAULT_NAMESPACE}
    [Documentation]    Get image status
    ${status}=    image_keywords.get image status    ${image_name}    ${namespace}
    RETURN    ${status}

Image is available for VM creation
    [Arguments]    ${image_name}    ${image_url}
    [Documentation]    Create an image from URL (delegates to Image module).
    Create image from url with name    ${image_name}    ${image_url}
    Wait for image downloaded by name    ${image_name}