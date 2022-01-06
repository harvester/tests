*** Settings ***
Resource            ../resources/login.robot
Resource            ../resources/hosts.robot
Library             yaml
Suite Setup         Login to Harvester Dashboard
Suite Teardown      Close All Browsers


*** Test Cases ***
Edit Host Configuration By Form
    [setup]     Navigate to Hosts And Record Nodes
    [template]  Edit Custom Name And Description
    FOR   ${idx}    ${node_row_id}  IN ENUMERATE   @{Nodes}   start=1
        ${node_row_id}      Custom-Name-Node${idx}  The description for ${idx} node
    END

Edit Host Configuration By YAML
    [tags]      yaml
    [setup]     Navigate to Hosts And Record Nodes
    [template]  Edit Custom Name And Description By YAML
    FOR   ${idx}    ${node_row_id}  IN ENUMERATE   @{Nodes}   start=1
        ${node_row_id}      YAML-CName-Node${idx}  Desc for ${idx} node By YAML
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

Edit Custom Name And Description
    [Teardown]      Purge Custom Name And Description on    ${row_id}
    [arguments]     ${row_id}       ${custom_name}      ${description}
    Given Click Hosts Option By Row     Edit Config     ${row_id}
    And Input Custom Name       ${custom_name}
    And Input Description       ${description}
    Then Click Save Button
    When Navigate To Option  Hosts
    Then Node Name ${custom_name} Should Be Available
    When Click Host Details By Name     ${custom_name}
    Then Field Custom Name In Basic Field Should Be     ${custom_name}
    When Click Config Button
    Then Value In Input Box Description Should Be       ${description}

Edit Custom Name And Description By YAML
    [Teardown]      Purge Custom Name And Description on    ${row_id}
    [arguments]     ${row_id}       ${custom_name}      ${description}
    Given Click Hosts Option By Row     Edit YAML     ${row_id}
    And Update YAML With    custom_name=${custom_name}      description=${description}
    Then Click Save Button In YAML
    When Navigate To Option  Hosts
    Then Node Name ${custom_name} Should Be Available
    When Click Host Details By Name     ${custom_name}
    Then Field Custom Name In Basic Field Should Be     ${custom_name}
    When Click Config Button
    Then Value In Input Box Description Should Be       ${description}


Input Custom Name
    [arguments]     ${txt}
    Input New Text  xpath://main//div[contains(@class, "edit")][./label[normalize-space(text())="Custom Name"]]/input
    ...             ${txt}

Input Description
    [arguments]     ${txt}
    Input New Text  xpath://main//div[contains(@class, "edit")][./label[normalize-space(text())="Description"]]/input
    ...             ${txt}

Click Save Button
    [arguments]     ${timeout}=${BROWSER_WAIT_TIMEOUT}
    Click Button    xpath://main//div[@class="buttons"]//button[./span[text()="Save"]]
    Wait Until Element Is Not Visible   xpath://main//div[@class="buttons"]//button[./span[text()="Save"]]  timeout=${timeout}
    # Message box:
    Wait Until Element Is Visible   xpath://div[@class="growl-list"]//i     timeout=${timeout}
    Click Element   xpath://div[@class="growl-list"]//i

Click Save Button In YAML
    [arguments]     ${timeout}=${BROWSER_WAIT_TIMEOUT}
    Click Button    xpath://main//div[@class="buttons"]//button[./span[text()="Save"]]
    Wait Until Element Is Not Visible   xpath://main//div[@class="buttons"]//button[./span[text()="Save"]]  timeout=${timeout}
    Sleep   2s

Node Name ${name} Should Be Available
    Element Should Be Visible   xpath://main//td[@data-title="Name"]//a[normalize-space(text())="${name}"]

Field Custom Name In Basic Field Should Be
    [arguments]         ${customized}
    ${displayed} =      Get Text   xpath://main//section[@id="basics"]//div[./div[normalize-space(text())="Custom Name"]]/div[@class="value"]
    Should Be Equal     ${displayed}    ${customized}

Click Config Button
    Click Button    xpath://main//header//button[./span[text()="Config"]]
    Sleep   0.3s
    Wait Until Element Is Visible   xpath://main//ul[@role="tablist"]
    # Wait Until Element Is Visible   xpath://main//button[@class="hide"]

Value In Input Box Description Should Be
    [arguments]         ${customized}
    ${displayed} =      Get Value   xpath://main//div[./label[normalize-space(text())="Description"]]/input
    Should Be Equal     ${displayed}    ${customized}

Purge Custom Name And Description on
    [arguments]         ${row_id}
    Given Click Hosts Option By Row     Edit Config     ${row_id}
    And Input Custom Name       ${EMPTY}
    And Input Description       ${EMPTY}
    Then Click Save Button

Update YAML With
    [arguments]     ${custom_name}      ${description}
    Wait Until Element Is Visible   css:main pre.CodeMirror-line    timeout=${BROWSER_WAIT_TIMEOUT}

    Click Element   css:main pre.CodeMirror-line
    Press Keys      css:main div.CodeMirror textarea
    ...             CTRL+a+CTRL+x
    ${yaml_txt} =   Paste String From Clipboard
    ${yaml_ctx} =   yaml.safe_load      ${yaml_txt}

    Update YAML     ${yaml_ctx}
    ...             metadata?annotations?harvesterhci.io/host-custom-name
    ...             ${custom_name}

    Update YAML     ${yaml_ctx}
    ...             metadata?annotations?field.cattle.io/description
    ...             ${description}

    ${new_yaml} =   yaml.safe_dump  ${yaml_ctx}
    Copy To Clipboard   ${new_yaml}
    Press Keys      css:main div.CodeMirror textarea
    ...             CTRL+a+CTRL+v
