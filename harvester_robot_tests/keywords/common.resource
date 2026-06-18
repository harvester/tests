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
    [Arguments]    ${prefix1}=${EMPTY}    ${prefix2}=${EMPTY}    ${precise}=${FALSE}
    [Documentation]    Generate a name with timestamp suffix and optional prefixes
    ...  The timestamp format is `%m%d%H%M` by default and `%m%d%H%M%S%f` when precise=${TRUE}
    ...  Examples:
    ...  Generate Unique Name            -> '06181015'
    ...  Generate Unique Name  foo       -> 'foo-06181015'
    ...  Generate Unique Name  foo  bar  precise=${TRUE}-> 'foo-bar-0618101519681156'
    ${name}=    common_keywords.generate_name_with_suffix    ${prefix1}    ${prefix2}    ${precise}
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
