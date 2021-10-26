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
