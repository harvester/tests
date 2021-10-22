*** Settings ***
Resource        common.robot


*** Variables ***
${USERNAME}       ${HARVESTER_USERNAME}
${PASSWORD}       ${HARVESTER_PASSWORD}


*** Keywords ***
Open Browser To Login Page
    Open Browser    ${LOGIN URL}    ${BROWSER}
    ...             options=add_argument("--ignore-certificate-errors")
    Wait Until Location Contains     dashboard/auth/login
    Title Should Be    Harvester
    Log Location

Input Username
    [Arguments]    ${username}
    Input Text      css:.labeled-input.edit > input[type='text']
    ...             ${username}

Input Password
    [Arguments]    ${password}
    Input Text      css:.labeled-input.edit > input[type='password']
    ...             ${password}

Submit Credentials
    Click Button    css:button[type=submit]
