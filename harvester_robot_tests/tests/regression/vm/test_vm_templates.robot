*** Settings ***
Documentation    VM Template Test Cases
...
...              Robot port of the system-default checks in
...              harvester_e2e_tests/apis/test_vm_templates.py
Test Tags        regression    virtualmachines    templates    pr-baseline

Library          Collections
Resource         ../../../keywords/common.resource
Resource         ../../../keywords/vm_template.resource

# Read-only suite: creates no resources, so no cleanup is needed. Must not use
# Common Suite Teardown - its global label sweep deletes resources still owned
# by sibling suites when running under pabot.
Suite Setup       Set Up Test Environment
Test Teardown     Common Test Teardown


*** Variables ***
# Default templates shipped in every supported version
@{BASE_TEMPLATES}
...    iso-image-base-template
...    raw-image-base-template
...    windows-iso-image-base-template
...    windows-raw-image-base-template
# Size-tiered Windows templates added in v1.9.0
@{WINDOWS_TIERED_TEMPLATES}
...    windows-iso-small-template
...    windows-iso-medium-template
...    windows-iso-large-template
...    windows-w11-iso-template


*** Test Cases ***
Test Get Not Exist Template
    [Tags]    p0    sanity    negative
    ${name}=    Generate Unique Name    template
    ${result}=    Try To Get Template    ${name}
    Operation Should Be Not Found    ${result}

Test Get System Default Templates
    [Tags]    p0    smoke
    ${names}=    List Default Template Names
    ${expected}=    Get Expected Default Templates
    Lists Should Be Equal    ${names}    ${expected}    ignore_order=${TRUE}
    ...    msg=Default templates do not match the expected set for this version

Test Get System Default Template Versions
    [Tags]    p0    smoke
    ${names}=    List Default Template Names
    ${refs}=    List Default Template Version References
    Lists Should Be Equal    ${names}    ${refs}    ignore_order=${TRUE}
    ...    msg=Default template versions do not reference the same template set


*** Keywords ***
Get Expected Default Templates
    [Documentation]    The exact default template set for the cluster's version:
    ...  the base four everywhere, plus the size-tiered Windows set on >= v1.9.0
    ${at_least_190}=    Cluster Version Is At Least    1.9.0
    IF    ${at_least_190}
        ${expected}=    Combine Lists    ${BASE_TEMPLATES}    ${WINDOWS_TIERED_TEMPLATES}
    ELSE
        ${expected}=    Copy List    ${BASE_TEMPLATES}
    END
    RETURN    ${expected}
