*** Settings ***
Library         SeleniumLibrary


*** Variables ***
${LOGIN URL}      ${HARVESTER_URL}
${BROWSER}        ${TESTING_BROWSER}


**** Keywords ***
Screenshot And Close Window
    Run Keyword If Test Passed  Capture Page Screenshot
    Close Window

Input New Text
    [Documentation]   Used to fix `Input Text` didn't do *clear* correctly.
    ...               ref: https://stackoverflow.com/questions/53518481/robot-framework-clear-element-text-keyword-is-not-working
    [arguments]   ${locator}   ${value}
    Press Keys      ${locator}      CTRL+a+BACKSPACE
    Input Text      ${locator}      ${value}
