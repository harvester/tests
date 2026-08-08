*** Settings ***
Documentation    Generic SSH Keywords
...    Shell access to Harvester nodes and to VMs. VMs are only reachable
...    from the node hosting them, so the VM keywords transparently tunnel
...    through that node.
Resource         variables.resource
Library          ../libs/keywords/ssh_keywords.py

*** Keywords ***
Generate SSH keypair
    [Documentation]    Generate an RSA keypair. Returns a dict with
    ...    `public_key` (feed to cloud-init) and `private_key` (to log in).
    ${keypair}=    ssh_keywords.generate_ssh_keypair
    RETURN    ${keypair}

Get VM IP address
    [Arguments]    ${vm_name}    ${network}=default
    [Documentation]    Return the IP the VM reports on the given network
    ${ip}=    ssh_keywords.get_vm_ip_address    ${vm_name}    ${network}
    RETURN    ${ip}

Get VM node IP
    [Arguments]    ${vm_name}
    [Documentation]    Return the IP of the Harvester node hosting the VM
    ${ip}=    ssh_keywords.get_vm_node_ip    ${vm_name}
    RETURN    ${ip}

Execute command on host
    [Arguments]    ${host_ip}    ${command}    &{options}
    [Documentation]    Run a command on a Harvester node, return its stdout.
    ...    Fails if the command exits non-zero.
    ${output}=    ssh_keywords.execute_command_on_host    ${host_ip}    ${command}    &{options}
    RETURN    ${output}

Execute command in VM
    [Arguments]    ${vm_name}    ${vm_user}    ${private_key}    ${command}    &{options}
    [Documentation]    Run a command inside a VM, return its stdout.
    ...    VMs are key-only, so ${private_key} is required. Pass
    ...    check=${FALSE} to tolerate a non-zero exit code.
    ${output}=    ssh_keywords.execute_command_in_vm
    ...    vm_name=${vm_name}    vm_user=${vm_user}    private_key=${private_key}
    ...    command=${command}    &{options}
    RETURN    ${output}

Execute command in VM and expect output
    [Arguments]    ${vm_name}    ${vm_user}    ${private_key}    ${command}    ${expected_output}    &{options}
    [Documentation]    Retry a command inside a VM until its stdout matches
    ...    ${expected_output}. Use this instead of a single Execute command in
    ...    VM whenever the VM needs time to catch up with a change already
    ...    applied through the API.
    ${output}=    ssh_keywords.execute_command_in_vm_and_expect_output
    ...    vm_name=${vm_name}    vm_user=${vm_user}    private_key=${private_key}
    ...    command=${command}    expected_output=${expected_output}    &{options}
    RETURN    ${output}

VM cloud-init should be done
    [Arguments]    ${vm_name}    ${vm_user}    &{options}
    [Documentation]    Wait until cloud-init has finished inside the VM
    ssh_keywords.wait_for_cloud_init_done    ${vm_name}    ${vm_user}    &{options}

