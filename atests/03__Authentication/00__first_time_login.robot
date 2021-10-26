**** Settings ***
Documentation       Used to test fresh Harvester installed.
Resource            ../resources/login.robot
Suite Setup         Open browser to login page
Suite Teardown      Set Password And Close Browser
Force Tags          setup password  smoke
Default Tags        positive



***** Variables ***
${SETUP_ENDPOINT}       # dashboard/auth/setup      # issue#1479
${SETUP_PAGE_URL}       ${HARVESTER_URL}${SETUP_ENDPOINT}
${CLIPBOARD_VALUE}



**** Test Cases ***
Random Password Copied
    Given Navigate To Setup Page
    And Click Copy Button
    Then Random Generated Password Should be Copied

Accept Term Is Required
    Given Navigate To Setup Page
    And Click Agree Terms As            ${True}
    Then Element Should Be Enabled      css:button[type=submit]

    And CLick Agree Terms As            ${False}
    Then Element Should Be Disabled     css:button[type=submit]

Accept Collection Of Anonymous Statistics Is Optional
    Given Navigate To Setup Page
          Click Agree Terms As          ${False}
    And Click Accept Collect Data As    ${True}
    Then Element Should Be Disabled     css:button[type=submit]

    And Click Accept Collect Data As    ${False}
    Then Element Should Be Disabled     css:button[type=submit]

Specific Password Inconsistant
    [tags]      negative
    Given Navigate To Setup Page
          Click Set Specific Password
    And Input New Password "THE PASSWORD" And confirm as "the password"
    Then Element Should Be Disabled     css:button[type=submit]

Specific Password Consistant
    Given Navigate To Setup Page
          Click Set Specific Password
    And Input New Password "THE_PASSWORD" And confirm as "THE_PASSWORD"
    Then Element Should Be Disabled     css:button[type=submit]
    And CLick Agree Terms As  ${True}
    Then Element Should Be Enabled      css:button[type=submit]

Random Password Regenerated
    Given Navigate To Setup Page
          Click Copy Button
    And Click Set Specific Password
        Click Use Randomly Generated Password
    Then Password In Clipboard Should Not Equals To New Password



**** Keywords ***
Set Password And Close Browser
    [tags]      done_setup
    [Teardown]  Close All Browsers
    Skip If     '${SUITE STATUS}' == 'SKIP'
    Run Keyword If All Tests Passed     Run Keywords
    ...         Navigate To Setup Page    timeout=5s
    ...   AND   Click Set Specific Password
    ...   AND   Input New Password "${HARVESTER_PASSWORD}" And confirm as "${HARVESTER_PASSWORD}"
    ...   AND   Click Agree Terms As  ${True}
    ...   AND   Click Button    css:button[type=submit]
    ...   AND   Wait Until Location Contains    io.dashboard    timeout=${BROWSER_WAIT_TIMEOUT}


Navigate To Setup Page
    [Arguments]     ${timeout}=${BROWSER_WAIT_TIMEOUT}
    Go To                           ${SETUP_PAGE_URL}
    Wait Until Location Contains    ${SETUP_ENDPOINT}
    Wait Until Element Is Visible   css:div.dashboard-root  ${timeout}
    Title Should Be                 Harvester

Click Set Specific Password
    Click Element   xpath://label[@class="radio-container"][span[contains(@aria-label, "specific")]]

Click Use Randomly Generated Password
    Click Element   xpath://label[@class="radio-container"][span[contains(@aria-label, "randomly")]]

Click Copy Button
    [return]    ${copied}
    Click Button            xpath://button[span[text()="Copy"]]
    ${copied} =             Paste String From Clipboard
    Set Suite Variable      ${CLIPBOARD_VALUE}      ${copied}

Click Agree Terms As
    [Arguments]     ${state}
    ${checked} =    Get Element Attribute   css:div.checkbox.eula span[role=checkbox]
    ...             aria-checked
    Log             Checked=${checked}, state=${state}   DEBUG
    ${checked} =    Convert To Boolean      ${checked}
    Run Keyword If  ${checked} != ${state}
    ...             Click Element   css:div.checkbox.eula span[role=checkbox]

Click Accept Collect Data As
    [Arguments]     ${state}
    ${checked} =    Get Element Attribute   css:div.checkbox:not(.eula) span[role=checkbox]
    ...             aria-checked
    Log             Checked=${checked}, state=${state}   DEBUG
    ${checked} =    Convert To Boolean      ${checked}
    Run Keyword If  ${checked} != ${state}
    ...             Click Element   css:div.checkbox:not(.eula) span[role=checkbox]

Input New Password "${new_pwd}" And confirm as "${confirm_pwd}"
    Input Password      xpath://label[starts-with(text(), "New")]/following-sibling::input
    ...                 ${new_pwd}
    Input Password      xpath://label[starts-with(text(), "Confirm")]/following-sibling::input
    ...                 ${confirm_pwd}

Random Generated Password Should be Copied
    ${copied} =                 Paste String From Clipboard
    Textfield Value Should Be   xpath://div[contains(@class, "disabled")][//span[contains(text(),"assword")]]/input
    ...                         ${copied}

Password In Clipboard Should Not Equals To New Password
    ${copied} =             Paste String From Clipboard
    Should Not Be Empty     ${copied}   Clipboard Is Empty !!!
    ${generated} =          Get Value   xpath://div[contains(@class, "disabled")][//span[contains(text(),"assword")]]/input
    Should Not Be Equal     ${copied}   ${generated}
