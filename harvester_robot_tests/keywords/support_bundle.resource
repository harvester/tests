*** Settings ***
Documentation    Support Bundle Keywords
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/support_bundle_keywords.py

*** Variables ***
${SUPPORT_BUNDLE_NAMESPACE}     harvester-system

*** Keywords ***
Support bundle is created
    [Arguments]    ${name}    ${description}=robot test support bundle
    [Documentation]    Create a support bundle in ${SUPPORT_BUNDLE_NAMESPACE}; it starts generating right away.
    support_bundle_keywords.create_support_bundle    ${name}    ${description}

Support bundle is deleted
    [Arguments]    ${name}
    [Documentation]    Delete a support bundle, ignoring when it is already gone.
    support_bundle_keywords.delete_support_bundle    ${name}
