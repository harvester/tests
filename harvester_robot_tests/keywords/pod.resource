*** Settings ***
Documentation    Pod Keywords
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/pod_keywords.py

*** Keywords ***
Create Pod
    [Arguments]    ${name}    ${namespace}    ${spec}
    [Documentation]    Create a pod from a spec dict.
    pod_keywords.create_pod    ${name}    ${namespace}    ${spec}

Wait For Pod Succeeded
    [Arguments]    ${name}    ${namespace}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until the pod reaches the Succeeded phase.
    pod_keywords.wait_for_pod_succeeded    ${name}    ${namespace}    ${timeout}

Get Pod Logs
    [Arguments]    ${name}    ${namespace}
    [Documentation]    Return the full log output of a pod as a string.
    ${logs}=    pod_keywords.get_pod_logs    ${name}    ${namespace}
    RETURN    ${logs}

Delete Pod If Exists
    [Arguments]    ${name}    ${namespace}
    [Documentation]    Delete a pod if it exists; silently ignores 404.
    pod_keywords.delete_pod_if_exists    ${name}    ${namespace}
