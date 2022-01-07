*** Settings ***
Resource            navigate.robot
Library             edit_yaml.py


*** Keywords ***
Click Hosts Option By Row
    [arguments]     ${option}   ${row_id}   ${timeout}=${BROWSER_WAIT_TIMEOUT}
    Navigate To Option      Hosts
    Click Button    xpath://main//tr[@data-node-id="${row_id}"]/td/button
    ${_opt} =   Convert To Title Case   ${option}
    ${_opt} =   Replace String      ${_opt}     Yaml    YAML
    Click Element   xpath://main//li[./span[text()="${_opt}"]]
    Sleep   0.5s
    Return From Keyword If  '${_opt}'.startswith("Download")

    Run Keyword If  '${_opt}'.startswith("Edit")
    ...             Wait Until Element Is Visible   css:main div.buttons    timeout=${timeout}
    ...     ELSE    Wait Until Element Is Visible   css:main section        timeout=${timeout}

Click Option ${option} On Node details
    Click Button    xpath://main//div[@class="actions"]/button
    ${_opt} =   Convert To Title Case   ${option}
    ${_opt} =   Replace String      ${_opt}     Yaml    YAML
    Click Element   xpath://main//li[./span[text()="${_opt}"]]
    Wait Until Element Is Visible   xpath://main//section   timeout=${BROWSER_WAIT_TIMEOUT}

Click Host Details By Name
    [arguments]     ${name}     ${timeout}=${BROWSER_WAIT_TIMEOUT}
    Click Link      xpath://main//td[@data-title="Name"]//a[normalize-space(text())="${name}"]
    Wait Until Element Is Visible   css:main section   timeout=${timeout}
