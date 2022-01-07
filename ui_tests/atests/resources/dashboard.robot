*** Settings ***
Resource            navigate.robot


*** Keywords ***
Click User Icon On Right Top
    [arguments]   ${timeout}=${BROWSER_WAIT_TIMEOUT}
    Navigate To Option   Dashboard   timeout=${timeout}
    Click Element   xpath://header//div[contains(@class, "user-image")]
    Sleep   0.3s

Click User Icon On Right Top Then Click Preferences
    [arguments]   ${timeout}=${BROWSER_WAIT_TIMEOUT}
    Click User Icon On Right Top     timeout=${timeout}
    Click Element   xpath://header//li[@class="user-menu-item"][a[text()="Preferences "]]

Click User Icon On Right Top Then Click Log Out
    [arguments]   ${timeout}=${BROWSER_WAIT_TIMEOUT}
    Click User Icon On Right Top     timeout=${timeout}
    Click Element    xpath://header//li[@class="user-menu-item"][a[text()="Log Out "]]
