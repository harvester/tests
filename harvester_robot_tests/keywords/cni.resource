*** Settings ***
Documentation    CNI Keywords - Reusable Keywords for CNI operations

Library          ../libs/keywords/cni_nad_keywords.py

*** Keywords ***

Create NetworkAttachmentDefinition
    [Arguments]    ${namespace}    ${name}    &{kwargs}
    [Documentation]    Create a NetworkAttachmentDefinition
    cni_nad_keywords.Create NAD    ${namespace}    ${name}    &{kwargs}

Delete NetworkAttachmentDefinition
    [Arguments]    ${namespace}    ${name}
    [Documentation]    Delete a NetworkAttachmentDefinition
    cni_nad_keywords.Delete NAD    ${namespace}    ${name}

NetworkAttachmentDefinition is Created
    [Arguments]    ${namespace}    ${name}    &{kwargs}
    [Documentation]    Create a new network
    ${nad}=    cni_nad_keywords.Get NAD    ${namespace}    ${name}
    Run Keyword If    ${nad} is None
    ...    Create NetworkAttachmentDefinition    ${namespace}    ${name}    &{kwargs}

NetworkAttachmentDefinition is Deleted
    [Arguments]    ${namespace}    ${name}
    [Documentation]    Delete a network
    ${nad}=    cni_nad_keywords.Get NAD    ${namespace}    ${name}
    Run Keyword If    ${nad} is not None
    ...    Delete NetworkAttachmentDefinition    ${namespace}    ${name}
