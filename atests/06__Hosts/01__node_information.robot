*** Settings ***
Resource            ../resources/login.robot
Resource            ../resources/navigate.robot
Suite Setup         Login to Harvester Dashboard
Suite Teardown      Close All Browsers


*** Test Cases ***
Node Basic Information
    [Template]  Verify ${node_row_id} Basic Information
    [setup]     Navigate to Hosts And Record Nodes
    FOR   ${node_row_id}  IN    @{Nodes}
        ${node_row_id}
    END

Node Resource Infomation
    [Template]  Verify ${node_row_id} Resources Information
    [setup]     Navigate to Hosts And Record Nodes
    FOR   ${node_row_id}   IN   @{Nodes}
        ${node_row_id}
    END


*** Keywords ***
Navigate to Hosts And Record Nodes
    Navigate To Option   Hosts
    List Available Nodes

List Available Nodes
    [return]        @{names}
    @{names} =      Execute Javascript
    ...             return Array.from(
    ...               document.querySelectorAll('main tbody tr')
    ...             ).map(e => e.getAttribute("data-node-id"))
    Set Test Variable   ${nodes}    ${names}

Verify ${node_row_id} Basic Information
    State of ${node_row_id} Should Be Active
    Name of ${node_row_id} Should Not Be Empty
    Host of ${node_row_id} IP Should Be Valid
    Age of ${node_row_id} Should Be Readable
    Disk of ${node_row_id} State Should Be Healthy

Verify ${node_row_id} Resources Information
    Given Navigate To Option        Hosts
    And Record CPU Values of        ${node_row_id}
    And Record Memory Values of     ${node_row_id}
    And Record Storage Values of    ${node_row_id}
    Then Navigate To Node           ${node_row_id}
         Displayed CPU Values Should Be Like       ${Record_cpu}
         Displayed Memory Values Should Be Like    ${Record_Mem}
         Displayed Storage Values Should Be Like   ${Record_storage}


State of ${node_row_id} Should Be ${state}
    Element Text Should Be   xpath://main//tr[@data-node-id="${node_row_id}"]//td[@data-title="State"]//span[contains(@class, "badge-state")]
    ...                      ${state}

Name of ${node_row_id} Should Not Be Empty
    ${name} =   Get Text    xpath://main//tr[@data-node-id="${node_row_id}"]//td[@data-title="Name"]//a
    Should Not Be Empty     ${name}

Host of ${node_row_id} IP Should Be Valid
    ${ipaddr} =   Get Text      xpath://main//tr[@data-node-id="${node_row_id}"]//td[@data-title="Host IP"]/div
    Import Library          ipaddress
    ipaddress.ip_address    ${ipaddr}

Age of ${node_row_id} Should Be Readable
    ${agetxt} =   Get Text      xpath://main//tr[@data-node-id="${node_row_id}"]//td[@data-title="Age"]/span
    Should Match Regexp     ${agetxt}   (\\d+(?:\\.\\d+)?)\\s+(sec|min|hour|day)s?
    Log     ${agetxt}

Disk of ${node_row_id} State Should Be ${state}
    Element Text Should Be   xpath://main//tr[@data-node-id="${node_row_id}"]//td[@data-title="Disk State"]//span
    ...                      ${state}

Record CPU Values of
    [arguments]     ${node_id}
    ${txt} =        Get Text      xpath://main//tr[@data-node-id="${node_id}"]//td[@data-title="CPU"]//span[span]
    ${matches} =    Get Regexp Matches
    ...             ${txt}
    ...             (\\d+(?:\\.\\d+)?)\\sof\\s(\\d+)    1   2
    Set Test Variable   ${Record_cpu}   ${matches}

Record Memory Values of
    [arguments]     ${node_id}
    ${txt} =        Get Text      xpath://main//tr[@data-node-id="${node_id}"]//td[@data-title="MEMORY"]//span[span]
    ${matches} =    Get Regexp Matches
    ...             ${txt}
    ...             (\\d+(?:\\.\\d+)?)\\sof\\s(\\d+)    1   2
    Set Test Variable   ${Record_Mem}   ${matches}

Record Storage Values of
    [arguments]     ${node_id}
    ${txt} =        Get Text      xpath://main//tr[@data-node-id="${node_id}"]//td[@data-title="Storage Size"]//span[span]
    ${matches} =    Get Regexp Matches
    ...             ${txt}
    ...             (\\d+(?:\\.\\d+)?)\\sof\\s(\\d+)    1   2
    Set Test Variable   ${Record_storage}   ${matches}

Navigate To Node
    [arguments]     ${node_id}      ${timeout}=${BROWSER_WAIT_TIMEOUT}
    Click Link      xpath://main//tr[@data-node-id="${node_id}"]//td[@data-title="Name"]//a
    Wait Until Element Is Visible   xpath://main//section     timeout=${timeout}
    sleep   0.5s

Displayed CPU Values Should Be Like
    [arguments]     ${old_value}
    ${txt} =        Get Text      //main//section//div[@class="numbers"][../h3[normalize-space(text())="CPU"]]/span[span]
    ${matches} =    Get Regexp Matches
    ...             ${txt}
    ...             (\\d+(?:\\.\\d+)?)\\sof\\s(\\d+)    1   2
    Should Be Equal     ${old_value}    ${matches}

Displayed Memory Values Should Be Like
    [arguments]     ${old_value}
    ${txt} =        Get Text      //main//section//div[@class="numbers"][../h3[normalize-space(text())="MEMORY"]]/span[span]
    ${matches} =    Get Regexp Matches
    ...             ${txt}
    ...             (\\d+(?:\\.\\d+)?)\\sof\\s(\\d+)    1   2
    Should Be Equal     ${old_value}    ${matches}

Displayed Storage Values Should Be Like
    [arguments]     ${old_value}
    ${txt} =        Get Text      //main//section//div[@class="numbers"][../h3[normalize-space(text())="Storage"]]/span[span]
    ${matches} =    Get Regexp Matches
    ...             ${txt}
    ...             (\\d+(?:\\.\\d+)?)\\sof\\s(\\d+)    1   2
    Should Be Equal     ${old_value}    ${matches}
