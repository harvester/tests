*** Settings ***
Documentation    VM Resource Update Test Cases
...    Port of harvester/tests test_3_vm_functions.py TestVMResource::test_update_cpu.
...    Verifies that a CPU core count change made via the API is actually
...    reflected inside the guest OS (via lscpu over SSH), not just in the
...    CRD spec, after the VM is restarted.
Test Tags        virtualmachines    regression

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/virtualmachine.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${IMG_NAME}        ${EMPTY}
${VM_NAME}         ${EMPTY}
${SSH_PUB_KEY}     ${EMPTY}
${SSH_PRI_KEY}     ${EMPTY}


*** Test Cases ***
Update VM CPU Cores
    [Tags]    p0
    [Documentation]    Changing a VM's CPU core count via the API must be
    ...    reflected inside the guest OS (lscpu) after the VM is restarted.
    ...    Proves the full path: API update -> KubeVirt -> libvirt/QEMU
    ...    domain -> guest kernel topology.
    VM is started    ${VM_NAME}
    VM should be running    ${VM_NAME}
    VM should have IP addresses    ${VM_NAME}
    VM cloud-init should be done    ${VM_NAME}    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}

    ${output}=    Execute Command In VM    ${VM_NAME}    lscpu -e=cpu | tail -1
    ...    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}
    ${output}=    Strip String    ${output}
    Should Be True    """${output}""".isdigit()
    ...    msg=Failed to list cpu amount, output: ${output}
    # lscpu -e=cpu lists one row per logical CPU (0, 1, 2, ...), so the
    # last line is the 0-based last CPU index: (+1) converts it to a count,
    # the second (+1) asks for one more core than the VM currently has.
    ${baseline}=    Evaluate    int($output) + 1
    ${new_cpus}=    Evaluate    ${baseline} + 1

    VM CPU is updated to ${new_cpus}    ${VM_NAME}
    VM is restarted    ${VM_NAME}
    VM should be running    ${VM_NAME}
    VM should have IP addresses    ${VM_NAME}
    VM cloud-init should be done    ${VM_NAME}    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}

    ${output}=    Execute Command In VM    ${VM_NAME}    lscpu -e=cpu | tail -1
    ...    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}
    ${output}=    Strip String    ${output}
    Should Be True    """${output}""".isdigit()
    ...    msg=Failed to list cpu amount, output: ${output}
    ${actual_cpus}=    Evaluate    int($output) + 1
    Should Be Equal As Integers    ${new_cpus}    ${actual_cpus}
    ...    msg=Failed to update CPU to ${new_cpus}, it still be ${actual_cpus}

    # Stop the VM so it's handed back to any following test in a known state
    VM is stopped    ${VM_NAME}
    VM should be stopped    ${VM_NAME}


Update VM USB Tablet
    [Tags]    p0
    [Documentation]    Port of harvester/tests test_3_vm_functions.py
    ...    TestVMResource::test_update_enable_usb.
    ...    Reads the current USB tablet state, changes it to the opposite,
    ...    verifies the change is reflected in the running VMI, then restores
    ...    the original state and verifies the restore.
    ...    Proves the full path: API update -> KubeVirt -> VMI spec without
    ...    assuming any particular initial state.

    # Step 1: Get the current USB Tablet status
    VM is started    ${VM_NAME}
    VM should be running    ${VM_NAME}
    ${enabled}=    Get VM USB Tablet Status    ${VM_NAME}

    # Step 2: Change the setting to the opposite state and verify
    IF    ${enabled}
        Disable VM USB Tablet    ${VM_NAME}
    ELSE
        Enable VM USB Tablet    ${VM_NAME}
    END
    VM is restarted    ${VM_NAME}
    VM should be running    ${VM_NAME}
    IF    ${enabled}
        VM USB Tablet should be disabled    ${VM_NAME}
    ELSE
        VM USB Tablet should be enabled    ${VM_NAME}
    END

    # Step 3: Recover the original setting and verify
    IF    ${enabled}
        Enable VM USB Tablet    ${VM_NAME}
    ELSE
        Disable VM USB Tablet    ${VM_NAME}
    END
    VM is restarted    ${VM_NAME}
    VM should be running    ${VM_NAME}
    IF    ${enabled}
        VM USB Tablet should be enabled    ${VM_NAME}
    ELSE
        VM USB Tablet should be disabled    ${VM_NAME}
    END
    VM is stopped    ${VM_NAME}
    VM should be stopped    ${VM_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}    img-${suffix}
    Set Suite Variable    ${VM_NAME}     vm-${suffix}
    Set up test environment
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    ${pub}    ${pri}=    Generate SSH Keypair
    Set Suite Variable    ${SSH_PUB_KEY}    ${pub}
    Set Suite Variable    ${SSH_PRI_KEY}    ${pri}
    # 1 CPU / 2Gi, Halted, with the SSH public key installed via cloud-init:
    # mirrors the pytest `stopped_vm` fixture
    VM is created    ${VM_NAME}    ${IMG_NAME}    1    2Gi
    ...    run_strategy=Halted    ssh_public_key=${SSH_PUB_KEY}

Local Suite Teardown
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}

