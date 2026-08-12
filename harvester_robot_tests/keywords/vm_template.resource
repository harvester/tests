*** Settings ***
Documentation    VM Template Keywords - Reusable keywords for VM template operations
Library          Collections
Library          ../libs/keywords/vm_template_keywords.py
Resource         variables.resource
Resource         common.resource


*** Variables ***
${DEFAULT_TEMPLATES_NAMESPACE}    harvester-public


*** Keywords ***
List Default Template Names
    [Documentation]    List names of the built-in VM templates in harvester-public
    ${names}=    vm_template_keywords.list_template_names    ${DEFAULT_TEMPLATES_NAMESPACE}
    RETURN    ${names}

List Default Template Version References
    [Documentation]    List template names referenced by the built-in template
    ...    versions (spec.templateId without the namespace prefix)
    ${refs}=    vm_template_keywords.list_template_version_references
    ...    ${DEFAULT_TEMPLATES_NAMESPACE}
    RETURN    ${refs}

Try To Get Template
    [Arguments]    ${template_name}    ${namespace}=${DEFAULT_TEMPLATES_NAMESPACE}
    [Documentation]    Attempt to get a template, returns a {success, code, message}
    ...    dict for the generic assertions in common.resource
    ${result}=    vm_template_keywords.try_get_template    ${template_name}    ${namespace}
    RETURN    ${result}
