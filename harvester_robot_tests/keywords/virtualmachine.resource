*** Settings ***
Documentation    VM Keywords
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/vm_keywords.py

*** Keywords ***
Create VM with name
    [Arguments]    ${vm_name}    &{config}
    [Documentation]    Create a virtual machine with provided name
    create vm    ${vm_name}    &{config}

Delete VM by name
    [Arguments]    ${vm_name}
    [Documentation]    Delete a VM
    delete vm    ${vm_name}

Start VM by name
    [Arguments]    ${vm_name}
    [Documentation]    Start a VM
    start vm    ${vm_name}

Stop VM by name
    [Arguments]    ${vm_name}
    [Documentation]    Stop a VM
    stop vm    ${vm_name}

Wait for VM running by name
    [Arguments]    ${vm_name}
    [Documentation]    Wait for VM to reach running state
    wait for vm running    ${vm_name}

Wait for VM stopped by name
    [Arguments]    ${vm_name}
    [Documentation]    Wait for VM to stop
    wait for vm stopped    ${vm_name}

Wait for VM deleted by name
    [Arguments]    ${vm_name}
    [Documentation]    Wait for VM to be deleted
    wait for vm deleted    ${vm_name}

Wait for VM IP addresses by name
    [Arguments]    ${vm_name}    ${networks}
    [Documentation]    Wait for VM to obtain IP addresses
    wait for vm ip addresses    ${vm_name}    ${networks}

Write data to VM by name
    [Arguments]    ${vm_name}    ${data_size_mb}=100
    [Documentation]    Write data to VM and return checksum
    ${checksum}=    write vm data    ${vm_name}    ${data_size_mb}
    RETURN    ${checksum}

Get VM data checksum by name
    [Arguments]    ${vm_name}
    [Documentation]    Get checksum of data in VM
    ${checksum}=    get vm data checksum    ${vm_name}
    RETURN    ${checksum}
