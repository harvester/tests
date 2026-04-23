*** Settings ***
Documentation    Image Keywords
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/image_keywords.py

*** Keywords ***
Create image from url with name
    [Arguments]    ${image_name}    ${image_url}    ${checksum}=
    [Documentation]    Create image from URL using provided name
    image_keywords.create image from url    ${image_name}    ${image_url}    checksum=${checksum}

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
