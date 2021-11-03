***** Settings ***
Resource            common.robot
Library             String


***** Keywords ***
Navigate To Advanced Option
    [arguments]     ${option}=Templates    ${timeout}=${BROWSER_WAIT_TIMEOUT}
    ${_opt} =   Convert To Title Case   ${option}
    Run Keyword If  '${_opt}' == 'Ssh Keys'     ${_opt} = SSH Keys
    Log     input:${option} convert to ${_opt}  INFO
    Click Element   css:div.nav div.header
    Click Element   xpath://a[./span[text()="${_opt}"]]
    Wait Until Element Is Visible   css:main div.outlet   ${timeout}
    Wait Until Element Is Visible   css:main div.outlet header   ${timeout}
    Wait Until Element Is Visible   css:main div.outlet div   ${timeout}
    Sleep   0.5s

Navigate To Advanced Settings And Edit Option
    [arguments]     ${option}    ${timeout}=${BROWSER_WAIT_TIMEOUT}
    Navigate To Advanced Option  Settings
    ${_opt} =   Convert To Lower Case   ${option}
    Click Element   xpath://h1[contains(text(), "${_opt}")]/../..//button
    Click Element   xpath://main/div/ul[//span[text()="Edit Setting"]]
    Wait Until Element Is Visible   css:main div.outlet   ${timeout}
    Wait Until Element Is Visible   css:main div.outlet div.masthead   ${timeout}
    Wait Until Element Is Visible   css:main div.outlet section   ${timeout}
    Sleep   0.5s

Navigate To Option
    [arguments]     ${option}       ${timeout}=${BROWSER_WAIT_TIMEOUT}
    ${_opt} =       Convert To Title Case   ${option}
    Log         Input:${option} conveted to ${_opt}   DEBUG
    Click Element   xpath://nav//li[a/span[text()="${option}"]]
    Sleep   0.2s
    Wait Until Element Is Not Visible   css:main div.loading-indicator   ${timeout}
    Sleep   0.3s
