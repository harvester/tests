*** Settings ***
Documentation       Simple example using SeleniumLibrary.
Metadata            Tested on Browser   ${BROWSER}
Metadata            Login URL           ${LOGIN_URL}
Metadata            Page Wait Timeout   ${BROWSER_WAIT_TIMEOUT}
Resource            ../resources/login.robot
Resource            ../resources/dashboard.robot
Suite Teardown      Close All Browsers
Force Tags          smoke
Default Tags        positive


*** Test Cases ***
InValid Login
    [tags]      negative
    [Setup]     Open Browser To Login Page
    [Teardown]  Screenshot And Close Window
    Given Input Login Username      something
          Input Login Password      not_correct
    And Submit Credentials
    Then Error Message Should Display

Valid Login
    [Setup]     Open Browser To Login Page
    [Teardown]  Screenshot And Close Window
    Given Open Browser To Login Page
          Input Login Username    ${HARVESTER_USERNAME}
          Input Login Password    ${HARVESTER_PASSWORD}
    And Submit Credentials
    Then Harvester Dashboard Should Be Display

Login Out From Valid Login
    [Setup]     Login To Harvester Dashboard
    [Teardown]  Screenshot And Close Window
    Given Click User Icon On Right Top
    Then Username Should Be  ${HARVESTER_USERNAME}
    And Click User Icon On Right Top Then Click Log Out
    Then User Should Be Log Out And Redirect To Log In Page


*** Keywords ***
Error Message Should Display
    Wait Until Element Is Visible   css:div.login-messages .banner.error
    Element Should COntain          css:div.login-messages .banner.error
    ...                             Invalid username or password

Username Should Be
    [arguments]     ${username}
    Element Attribute Value Should Be   //header//div[@class="user-name"]
    ...                                 innerText   \ ${username}

User Should Be Log Out And Redirect To Log In Page
    Wait Until Location Contains    dashboard/auth/login
