*** Settings ***
Documentation    ConfigMap Keywords
Library          ../libs/keywords/configmap_keywords.py


*** Keywords ***
Config map is created
    [Arguments]    ${name}    ${namespace}=default    ${labels}=${NONE}    ${data}=${NONE}
    [Documentation]    Create a config map in ${namespace}, with optional extra labels (dict)
    ...    and data (dict)
    configmap_keywords.create config map    ${name}    ${namespace}    ${labels}    ${data}

Config map is deleted
    [Arguments]    ${name}    ${namespace}=default
    [Documentation]    Delete a config map (idempotent)
    configmap_keywords.delete config map    ${name}    ${namespace}
