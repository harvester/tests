*** Settings ***
Documentation    Common Keywords
Library          ../libs/keywords/common_keywords.py
Resource         variables.resource


*** Keywords ***
Set up test environment
    [Documentation]    Initialize test environment
    Log    Setting up test environment
    common_keywords.init harvester api client    ${HARVESTER_ENDPOINT}    ${HARVESTER_USERNAME}    ${HARVESTER_PASSWORD}
    common_keywords.init k8s api client

Cleanup test resources
    [Documentation]    Clean up all resources created during tests
    Log    Cleaning up test resources
    Run Keyword And Ignore Error    common_keywords.Cleanup VMs
    Run Keyword And Ignore Error    common_keywords.Cleanup volumes
    Run Keyword And Ignore Error    common_keywords.Cleanup images
    Run Keyword And Ignore Error    common_keywords.Cleanup networks
    Run Keyword And Ignore Error    common_keywords.Cleanup backups

List Pods By Label
    [Arguments]    ${namespace}    ${label_selector}   ${status}=${None}
    [Documentation]    Get pods by label selector
    ${pods}=    common_keywords.list_pods_by_label    ${namespace}    ${label_selector}    ${status}
    RETURN    ${pods}

Count Pods By Label
    [Arguments]    ${namespace}    ${label_selector}   ${status}=${None}
    [Documentation]    Get pods by label selector
    ${pods}=    common_keywords.list_pods_by_label    ${namespace}    ${label_selector}    ${status}
    ${count}=   Get Length    ${pods}
    RETURN    ${count}
