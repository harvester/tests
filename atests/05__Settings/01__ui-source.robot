***** Settings ***
Resource            ../resources/login.robot
Resource            ../resources/navigate.robot
Suite Setup         Login to Harvester Dashboard
Suite Teardown      Close All Browsers


**** Test Cases ***
Default UI Source
    [setup]     Navigate To Advanced Settings And Edit Option   ui-source
    Given Click Combobox And Select Option      Bundled
    And Value Should Be   Bundled
    Then Click Use the default Value Button
         Value Should Be   Auto

External UI Source
    [setup]     Navigate To Advanced Settings And Edit Option   ui-source
    Given Click Combobox And Select Option      External
    And Click Save Button
        Capture Page Screenshot
    And Close Browser
    Then Login to Harvester Dashboard
         Scripts Src in Head should Starts With   https://releases.rancher.com

Bundled UI Source
    [setup]     Navigate To Advanced Settings And Edit Option   ui-source
    Given Click Combobox And Select Option      Bundled
    And Click Save Button
        Capture Page Screenshot
    And Close Browser
    Then Login to Harvester Dashboard
         Scripts Src in Head should Starts With   ${HARVESTER_URL}


**** Keywords ***
Click Combobox And Select Option
    [arguments]     ${option}
    Click Element   xpath://section//div[@role="combobox"]
    Click Element   xpath://ul[@role="listbox"]/li[./div[contains(text(), "${option}")]]

Click Use the default Value Button
    Click Button    xpath://section/form//button[contains(text(), "default value")]

Click Save Button
    Click Button    xpath://section//button[./span[text()="Save"]]

Scripts Src in Head should Starts With
    [arguments]     ${url}
    @{result} =     Execute Javascript
    ...             var items = [];
    ...             document.querySelectorAll("script[src]").forEach(e => items.push(e.src));
    ...             document.querySelectorAll("link[href]").forEach(e => items.push(e.href));
    ...             return items;
    Log     ${result}   DEBUG
    FOR   ${href}   IN   @{result}
        Should Start With   ${href}   ${url}
    END

Value Should Be
    [arguments]     ${value}
    Element Text Should Be      xpath://section/form//div[@role="combobox"]//span
    ...                         ${value}
