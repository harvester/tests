***** Settings ***
Resource            ../resources/login.robot
Resource            ../resources/navigate.robot
Suite Setup         Login to Harvester Dashboard
Suite Teardown      Close All Browsers


**** Test Cases ***
Test Advanced Navigation
    [template]      Navigate To Advanced Option ${option} And Screenshot
    Settings
    Backups
    Networks
    SSH Keys
    Cloud Config Templates
    Templates

Test Advanced Settings Navigation
    [template]      Navigate To Edit Advanced Setting ${option} And Screenshot
    ui-index
    server-url
    ui-source
    vlan
    upgrade-checker-url
    upgrade-checker-enabled
    LOG-LEVEL
    backup-target


**** Keywords ***
Navigate To Advanced Option ${option} And Screenshot
    Navigate To Advanced    ${option}
    Capture Page Screenshot

Navigate To Edit Advanced Setting ${option} And Screenshot
    Navigate To Advanced Settings And Edit Option   ${option}
    Capture Page Screenshot
