*** Settings ***
Resource            ../resources/login.robot
Resource            ../resources/navigate.robot
Suite Teardown      Close All Browsers


*** Variables ***
${ORIGIN_URL}           ${{ '${HARVESTER_URL}'.strip('/') }}
${ENDPOINT_IS_LOGIN}    dashboard/c/local
${ENDPOINT_NOT_LOGIN}   dashboard/auth/login


*** Test Cases ***
Harvester Icon Position
    [Setup]         Login to Harvester Dashboard
    [Teardown]      Close Browser
    Given Navigate To Option    Dashboard

    Then Icon Position Should Be In OffsetLeft 0 And OffsetTop 0
    And Icon Should Be Named    harvester.svg
    # TODO: Compare svg's content?

Harvester Dashboard URL Redirect With Login
    [Teardown]      Close Browser
    Given Login to Harvester Dashboard
    Then URL Location Should Starts With    ${ORIGIN_URL}/${ENDPOINT_IS_LOGIN}

    And Navigate To Location                ${ORIGIN_URL}
    Then URL Location Should Starts With    ${ORIGIN_URL}/${ENDPOINT_IS_LOGIN}

Harvester Dashboard URL Redirect Without Login
    [Teardown]      Close Browser
    Given Open Browser To Login Page
    And Navigate To Location                ${ORIGIN_URL}/${ENDPOINT_IS_LOGIN}
    Then URL Location Should Starts With    ${ORIGIN_URL}/${ENDPOINT_NOT_LOGIN}


*** Keywords ***
Icon Position Should Be In OffsetLeft ${left} And OffsetTop ${top}
    Element Attribute Value Should Be   xpath://header/div[//img[@class="side-menu-logo"]]
    ...                                 offsetLeft  ${left}

    Element Attribute Value Should Be   xpath://header/div[//img[@class="side-menu-logo"]]
    ...                                 offsetTop   ${top}

Icon Should Be Named
    [arguments]         ${name}
    ${link} =   Get Element Attribute   xpath://header//img[@class="side-menu-logo"]   src
    Should End With     ${link}     ${name}

URL Location Should Starts With
    [arguments]         ${url}
    ${current_url} =    Get Location
    Should Start With   ${current_url}      ${url}


Navigate To Location
    [arguments]         ${url}
    Go To   ${url}
    Wait Until Element Is Not Visible       xpath://i[@class="initial-load-spinner"]
    Sleep   0.2s
