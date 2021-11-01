*** Settings ***
Resource            common.robot
Library             login_utils.py


*** Keywords ***
Open Browser To Login Page
    [Arguments]     ${endpoint}=dashboard/auth/login
    ...             ${timeout}=${BROWSER_WAIT_TIMEOUT}

    Open Browser    ${LOGIN URL}    ${BROWSER}
    ...             options=add_argument("--ignore-certificate-errors")
    Wait Until Location Contains     ${endpoint}    timeout=${timeout}
    Title Should Be    Harvester
    Log Location

Input Login Username
    [Arguments]    ${username}
    Input Text      css:.labeled-input.edit > input[type='text']
    ...             ${username}

Input Login Password
    [Arguments]    ${password}
    Input Text      css:.labeled-input.edit > input[type='password']
    ...             ${password}

Submit Credentials
    Click Button    css:button[type=submit]

Harvester Dashboard Should Be Display
    Wait Until Location Does Not Contain    auth/login
    ...                                     timeout=${BROWSER_WAIT_TIMEOUT}
    Location Should Contain     harvesterhci.io.dashboard
    Wait Until Element Is Visible   css:main div.outlet   ${BROWSER_WAIT_TIMEOUT}

Login to Harvester Dashboard
    Given Open Browser To Login Page
          Input Login Username    ${HARVESTER_USERNAME}
          Input Login Password    ${HARVESTER_PASSWORD}
    And Submit Credentials
    Then Harvester Dashboard Should Be Display
