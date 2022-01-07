*** Settings ***
Library         SeleniumLibrary


*** Variables ***
${LOGIN URL}      ${HARVESTER_URL}
${BROWSER}        ${TESTING_BROWSER}
${DOWNLOAD_TIMEOUT}     20m

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


Check File Is Downloaded
    [Teardown]      Go Back
    Sleep           3s
    Go To           chrome://downloads/
    Sleep           1s
    ${_timeout} =   Get Selenium Timeout
    Set Selenium Timeout    ${DOWNLOAD_TIMEOUT}
    ${result} =     Execute Async Javascript
    ...             var callback = arguments[arguments.length - 1];
    ...             var mgr = document.querySelector('downloads-manager').shadowRoot;
    ...             var item = mgr.querySelector('downloads-item').shadowRoot;
    ...             var show_btn = item.getElementById('show');
    ...             var retry_btn = item.querySelector('cr-button[focus-type="retry"]');
    ...             var retries = 3;
    ...             setInterval(() => {
    ...                 if (show_btn.parentElement.hidden === false) {
    ...                     callback(item.querySelector("#name").innerText);
    ...                 } else if (!retry_btn.parentElement.hidden && retries > 0) {
    ...                     retries--;
    ...                     retry_btn.click();
    ...                 } else if (retries < 0) {
    ...                     callback("download failed");
    ...                 }
    ...             }, 3000);
    Set Selenium Timeout    ${_timeout}
    Should Not Be Empty     ${result}
    Log     File ${result} Downloaded.
