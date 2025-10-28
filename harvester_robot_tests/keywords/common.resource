*** Settings ***
Documentation    Common Keywords
Resource         variables.resource
Library          ../libs/keywords/common_keywords.py

*** Keywords ***
Set up test environment
    [Documentation]    Initialize test environment
    Log    Setting up test environment
    init harvester api client    ${HARVESTER_ENDPOINT}    ${HARVESTER_USERNAME}    ${HARVESTER_PASSWORD}
    init k8s api client

Cleanup test resources
    [Documentation]    Clean up all resources created during tests
    Log    Cleaning up test resources
    Run Keyword And Ignore Error    common_keywords.Cleanup VMs
    Run Keyword And Ignore Error    common_keywords.Cleanup images
    Run Keyword And Ignore Error    common_keywords.Cleanup volumes
    Run Keyword And Ignore Error    common_keywords.Cleanup networks
    Run Keyword And Ignore Error    common_keywords.Cleanup backups
