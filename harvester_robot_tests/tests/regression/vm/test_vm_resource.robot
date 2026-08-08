*** Settings ***
Documentation    VM Resource Update Test Cases
...    Port of harvester/tests test_3_vm_functions.py TestVMResource
...    (test_update_cpu).
Test Tags        virtualmachines    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/virtualmachine.resource
Resource    ../../../keywords/ssh.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${IMG_NAME}           ${EMPTY}
${VM_NAME}            ${EMPTY}
${SSH_PUBLIC_KEY}     ${EMPTY}
${SSH_PRIVATE_KEY}    ${EMPTY}

# Default cloud-init user of the openSUSE Leap NoCloud image
${VM_SSH_USER}        %{VM_SSH_USER=opensuse}


*** Test Cases ***
Update VM CPU Cores
    [Tags]    p0
    [Documentation]    Update the CPU cores of a running VM and verify the
    ...    change actually reaches the VM. The VM spec is only a request, so
    ...    the VM is logged into over SSH and `lscpu` is used to count the
    ...    CPUs it really has, both before and after the update. The change
    ...    takes effect only after a restart.
    ...    `lscpu -e=cpu | tail -1` prints the highest CPU index, which is one
    ...    less than the CPU count. The `=` is escaped as `\=` so Robot does
    ...    not parse the command as a named argument.

    # The VM was created with 1 CPU, so the last CPU index is 0.
    Execute command in VM and expect output
    ...    vm_name=${VM_NAME}
    ...    vm_user=${VM_SSH_USER}
    ...    private_key=${SSH_PRIVATE_KEY}
    ...    command=lscpu -e\=cpu | tail -1
    ...    expected_output=0

    VM CPU is updated    ${VM_NAME}    2

    # Spec is updated immediately, the running VM is not.
    ${spec_cores}=    Get VM CPU Cores    ${VM_NAME}
    Should Be Equal As Integers    ${spec_cores}    2

    VM is restarted    ${VM_NAME}
    VM should be running    ${VM_NAME}
    VM should have IP addresses    ${VM_NAME}
    VM qemu-agent should be connected    ${VM_NAME}

    # The VMI reports the new topology...
    VM CPU cores should be    ${VM_NAME}    2

    # ...and so does the VM itself, which is what the user observes:
    # 2 CPUs means the last CPU index is 1.
    Execute command in VM and expect output
    ...    vm_name=${VM_NAME}
    ...    vm_user=${VM_SSH_USER}
    ...    private_key=${SSH_PRIVATE_KEY}
    ...    command=lscpu -e\=cpu | tail -1
    ...    expected_output=1

    # The original test leaves the VM stopped.
    VM is stopped    ${VM_NAME}
    VM should be stopped    ${VM_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}    img-${suffix}
    Set Suite Variable    ${VM_NAME}     vm-${suffix}
    Set up test environment

    # The stock cloud images ship no usable credentials, so an SSH key is
    # generated and injected via cloud-init at creation time.
    ${keypair}=    Generate SSH keypair
    Set Suite Variable    ${SSH_PUBLIC_KEY}     ${keypair}[public_key]
    Set Suite Variable    ${SSH_PRIVATE_KEY}    ${keypair}[private_key]

    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}

    VM is created    ${VM_NAME}    ${IMG_NAME}    1    4Gi
    ...    ssh_public_key=${SSH_PUBLIC_KEY}
    VM should be running    ${VM_NAME}
    VM should have IP addresses    ${VM_NAME}
    VM qemu-agent should be connected    ${VM_NAME}
    VM cloud-init should be done    ${VM_NAME}    ${VM_SSH_USER}
    ...    private_key=${SSH_PRIVATE_KEY}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}

