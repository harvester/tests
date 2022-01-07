*** Settings ***
Resource            ../resources/login.robot
Resource            ../resources/hosts.robot
Library             OperatingSystem
Library             yaml
Suite Setup         Login to Harvester Dashboard
Suite Teardown      Close All Browsers


*** Test Cases ***
Download YAML One By One
    [setup]     Navigate to Hosts And Record Nodes
    [template]  Verify YAML Downloaded From
    FOR     ${node_row_id}  IN      @{Nodes}
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

Verify YAML Downloaded From
    [arguments]     ${row_id}
    Given Click Hosts Option By Row     Download YAML   ${row_id}
    And Get Node Name From Row   ${row_id}
    Then Check File Is Downloaded And Named     ${node_name}
    And File Content Should Be Valid YAML

Get Node Name From Row
    [arguments]         ${row_id}
    [return]            ${name}
    ${name} =           Get Text    xpath://main//tr[@data-node-id="${row_id}"]//td[@data-title="Name"]//a
    Set Test Variable   ${node_name}    ${name}

Check File Is Downloaded And Named
    [arguments]     ${name}
    Check File Is Downloaded
    Wait Until Element Is Not Visible   css:i.initial-load-spinner  timeout=${BROWSER_WAIT_TIMEOUT}
    File Should Exist   ${BROWSER_DOWNLOAD_PATH}/${name}.yaml
    Set Test Variable   ${filename}    ${name}.yaml

File Content Should Be Valid YAML
    ${ctx} =        Get File  ${BROWSER_DOWNLOAD_PATH}/${filename}
    yaml.safe_load  ${ctx}
