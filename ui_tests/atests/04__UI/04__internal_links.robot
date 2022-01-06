*** Settings ***
Resource            ../resources/login.robot
Resource            ../resources/navigate.robot
Suite Teardown      Close All Browsers


*** Test Cases ***
Links In Dashboard
    [Setup]         Login to Harvester Dashboard
    [Teardown]      Close Browser
    [Template]      Link Box of ${Link_Name} Should Navigate To Page ${Nav_Name}
    Hosts               Hosts
    Virtual Machines    Virtual Machines
    Networks            Networks
    Images              Images
    Volumes             Volumes


*** Keywords ***
Link Box of ${Link_Name} Should Navigate To Page ${Nav_Name}
    Given Navigate To Page ${Nav_Name} And Record URL
    And Navigate To Option  Dashboard
    When Click ${Link_Name} Link Box
    Then Current URL Should Be Equal To Record URL

Navigate To Page ${Page} And Record URL
    [Teardown]              Click Element       xpath://nav//i[contains(@class, 'toggle')]
    Click Element           xpath://nav//i[contains(@class, 'toggle')]
    Navigate To Option      ${Page}
    ${nav_url} =    Get Location
    Set Test Variable       ${page_url}      ${nav_url}

Click ${name} Link Box
    Sleep   1s
    Click Element   xpath://main//div[contains(@class, "has-link")][.//h3[normalize-space(text())="${name}"]]
    Sleep   0.2s
    Wait Until Element Is Not Visible   css:main div.loading-indicator   ${BROWSER_WAIT_TIMEOUT}
    Sleep   0.3s

Current URL Should Be Equal To Record URL
    ${current_url} =        Get Location
    Should Be Equal     ${page_url}     ${current_url}
