*** Settings ***
Documentation    Deployment Keywords
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/deployment_keywords.py

*** Keywords ***
Wait For Deployment Ready
    [Arguments]    ${name}    ${namespace}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for a Deployment to report all replicas ready
    ...               Args:
    ...                   name: Name of the deployment
    ...                   namespace: Kubernetes namespace
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for deployment ${namespace}/${name} to be ready
    deployment_keywords.wait_for_deployment_ready    ${name}    ${namespace}    ${timeout}
    Log    Deployment ${namespace}/${name} is ready

Wait For Deployment Gone
    [Arguments]    ${name}    ${namespace}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for a Deployment to be removed
    ...               Args:
    ...                   name: Name of the deployment
    ...                   namespace: Kubernetes namespace
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for deployment ${namespace}/${name} to be gone
    deployment_keywords.wait_for_deployment_gone    ${name}    ${namespace}    ${timeout}
    Log    Deployment ${namespace}/${name} is gone
