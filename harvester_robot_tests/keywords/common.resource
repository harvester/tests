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

Generate Unique Name
    [Arguments]    ${prefix1}=${EMPTY}    ${prefix2}=${EMPTY}
    [Documentation]    Generate a unique name with optional prefixes and yymmdd-HHMMSS-ffffqa timestamp suffix
    ...  Generate Unique Name            -> '260603-145834-1273qa'
    ...  Generate Unique Name  foo       -> 'foo-260603-145834-1273qa'
    ...  Generate Unique Name  foo  bar  -> 'foo-bar-2260603-145834-1273qa'
    ${name}=    common_keywords.generate_name_with_suffix    ${prefix1}    ${prefix2}
    RETURN    ${name}

Cleanup test resources
    [Documentation]    Clean up all resources created during tests
    Log    Cleaning up test resources
    Run Keyword And Ignore Error    common_keywords.cleanup_vms
    Run Keyword And Ignore Error    common_keywords.cleanup_volumes
    Run Keyword And Ignore Error    common_keywords.cleanup_images
    Run Keyword And Ignore Error    common_keywords.cleanup_storageclasses
    Run Keyword And Ignore Error    common_keywords.cleanup_networks
    Run Keyword And Ignore Error    common_keywords.cleanup_backups

Common Suite Teardown
    Run Keyword If All Tests Passed    Cleanup test resources
    Run Keyword If Any Tests Failed    Log Variables

Common Test Teardown
    Run Keyword If Test Failed    Log Variables

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
