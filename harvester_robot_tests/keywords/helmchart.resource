*** Settings ***
Documentation    HelmChart Keywords
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/helmchart_keywords.py

*** Keywords ***
Create GPU Operator HelmChart
    [Arguments]    ${name}    ${namespace}    ${target_namespace}
    [Documentation]    Create the GPU Operator HelmChart CR in ${namespace}.
    helmchart_keywords.create_gpu_operator_helmchart    ${name}    ${namespace}    ${target_namespace}

Wait For HelmChart Deployed
    [Arguments]    ${name}    ${namespace}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until the HelmChart install Job completes successfully.
    helmchart_keywords.wait_for_helmchart_deployed    ${name}    ${namespace}    ${timeout}

Delete HelmChart
    [Arguments]    ${name}    ${namespace}
    [Documentation]    Delete a HelmChart CR and wait for full removal.
    helmchart_keywords.delete_helmchart    ${name}    ${namespace}
