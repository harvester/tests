*** Settings ***
Documentation    VM Delete Protection Test Cases
...    Covers VM delete protection (harvester/harvester#12137). It uses the KubeVirt
...    label kubevirt.io/vm-delete-protection, the same as KubeVirt's SSP operator:
...    - a VM labelled "true" or "True" cannot be deleted until the label is
...    changed; other values such as "TRUE" or "1" do not protect it
...    - the default-vm-delete-protection setting labels new VMs only, respects an
...    explicit "false", and skips VMs created by the Rancher node driver / CAPHV
...    VMs are created stopped: delete protection does not depend on the VM running.
Test Tags        virtualmachines    regression

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/setting.resource
Resource    ../../../keywords/virtualmachine.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# StorageClass for the test image. Empty uses the cluster default; override
# (e.g. --variable IMAGE_STORAGE_CLASS:lvm-thin) on clusters whose default
# storage cannot fit the test volumes.
${IMAGE_STORAGE_CLASS}    ${EMPTY}

${PROTECTION_LABEL}       kubevirt.io/vm-delete-protection
${DEFAULT_SETTING}        default-vm-delete-protection
${CREATOR_LABEL}          harvesterhci.io/creator
${NODE_DRIVER_CREATOR}    docker-machine-driver-harvester
${PROTECTED_MESSAGE}      has delete protection enabled

# Dynamic Variables
${IMG_NAME}           ${EMPTY}
${VM_PROTECTED}       ${EMPTY}
${VM_CAPITAL}         ${EMPTY}
${VM_EXISTING}        ${EMPTY}
${VM_DEFAULTED}       ${EMPTY}
${VM_OPT_OUT}         ${EMPTY}
${VM_NODE_DRIVER}     ${EMPTY}


*** Test Cases ***
Protected VM Cannot Be Deleted
    [Tags]    p0
    [Documentation]    A VM labelled kubevirt.io/vm-delete-protection=true is refused
    ...    by the admission webhook, with a message saying protection must be
    ...    disabled first, and the VM is left in place.
    Protected VM is created    ${VM_PROTECTED}    true
    ${result}=    Try To Delete VM    ${VM_PROTECTED}
    Operation Should Be Rejected    ${result}    ${PROTECTED_MESSAGE}    ${PROTECTION_LABEL}
    VM label should be    ${VM_PROTECTED}    ${PROTECTION_LABEL}    true

Disabling Delete Protection Allows Deletion
    [Tags]    p0
    [Documentation]    Setting the label to "false" turns protection off and the
    ...    VM can then be deleted.
    VM label is set    ${VM_PROTECTED}    ${PROTECTION_LABEL}    false
    VM is deleted    ${VM_PROTECTED}
    VM should be deleted    ${VM_PROTECTED}

Capitalized True Also Protects The VM
    [Tags]    p1
    [Documentation]    Same match as the KubeVirt SSP policy: "True" protects too.
    Protected VM is created    ${VM_CAPITAL}    True
    ${result}=    Try To Delete VM    ${VM_CAPITAL}
    Operation Should Be Rejected    ${result}    ${PROTECTED_MESSAGE}
    VM label is set    ${VM_CAPITAL}    ${PROTECTION_LABEL}    ${None}
    VM is deleted    ${VM_CAPITAL}
    VM should be deleted    ${VM_CAPITAL}

Other Label Values Do Not Protect The VM
    [Tags]    p2    negative
    [Documentation]    Only "true" and "True" enable protection, as in the KubeVirt
    ...    SSP policy, so a VM labelled "TRUE" or "1" can be deleted.
    FOR    ${value}    IN    TRUE    1
        Protected VM is created    ${VM_CAPITAL}    ${value}
        VM is deleted    ${VM_CAPITAL}
        VM should be deleted    ${VM_CAPITAL}
    END

Default Setting Protects Only New VMs
    [Tags]    p0
    [Documentation]    With default-vm-delete-protection=true, a VM created
    ...    afterwards gets the label "true", a VM created with an explicit "false"
    ...    keeps it, and a VM that existed before the change is not touched.
    VM is created    ${VM_EXISTING}    ${IMG_NAME}    1    1Gi    run_strategy=Halted
    VM label should be absent    ${VM_EXISTING}    ${PROTECTION_LABEL}
    setting_keywords.update    ${DEFAULT_SETTING}    true
    VM is created    ${VM_DEFAULTED}    ${IMG_NAME}    1    1Gi    run_strategy=Halted
    VM label should be    ${VM_DEFAULTED}    ${PROTECTION_LABEL}    true
    ${result}=    Try To Delete VM    ${VM_DEFAULTED}
    Operation Should Be Rejected    ${result}    ${PROTECTED_MESSAGE}
    Protected VM is created    ${VM_OPT_OUT}    false
    VM label should be    ${VM_OPT_OUT}    ${PROTECTION_LABEL}    false
    VM label should be absent    ${VM_EXISTING}    ${PROTECTION_LABEL}
    [Teardown]    Reset Default Delete Protection

Rancher Node Driver VMs Are Not Protected By Default
    [Tags]    p1
    [Documentation]    VMs created by the Rancher node driver or CAPHV
    ...    (harvesterhci.io/creator=docker-machine-driver-harvester) must stay
    ...    deletable by Rancher, so the default setting does not label them.
    setting_keywords.update    ${DEFAULT_SETTING}    true
    ${labels}=    Create Dictionary    ${CREATOR_LABEL}=${NODE_DRIVER_CREATOR}
    VM is created    ${VM_NODE_DRIVER}    ${IMG_NAME}    1    1Gi    run_strategy=Halted
    ...    labels=${labels}
    VM label should be absent    ${VM_NODE_DRIVER}    ${PROTECTION_LABEL}
    VM is deleted    ${VM_NODE_DRIVER}
    VM should be deleted    ${VM_NODE_DRIVER}
    [Teardown]    Reset Default Delete Protection

Invalid Default Setting Value Is Rejected
    [Tags]    p2    negative
    [Documentation]    The setting only accepts boolean values ("true", "false",
    ...    "True", "1", ...); "yes" is rejected.
    Run Keyword And Expect Error    *Failed to update setting*
    ...    setting_keywords.update    ${DEFAULT_SETTING}    yes
    ${value}=    setting_keywords.get_value    ${DEFAULT_SETTING}
    Should Not Be Equal As Strings    ${value}    yes


*** Keywords ***
Protected VM is created
    [Arguments]    ${vm_name}    ${value}
    [Documentation]    Create a stopped VM with the delete protection label set to value
    ${labels}=    Create Dictionary    ${PROTECTION_LABEL}=${value}
    VM is created    ${vm_name}    ${IMG_NAME}    1    1Gi    run_strategy=Halted
    ...    labels=${labels}

Reset Default Delete Protection
    Run Keyword And Ignore Error    setting_keywords.reset    ${DEFAULT_SETTING}
    Common Test Teardown

Unprotect And Delete VM
    [Arguments]    ${vm_name}
    [Documentation]    Cleanup: protection must be removed before a VM can be deleted
    Run Keyword And Ignore Error    VM label is set    ${vm_name}    ${PROTECTION_LABEL}    false
    Run Keyword And Ignore Error    VM is deleted    ${vm_name}

Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}          img-${suffix}
    Set Suite Variable    ${VM_PROTECTED}      vm-dp-${suffix}
    Set Suite Variable    ${VM_CAPITAL}        vm-dp-cap-${suffix}
    Set Suite Variable    ${VM_EXISTING}       vm-dp-old-${suffix}
    Set Suite Variable    ${VM_DEFAULTED}      vm-dp-new-${suffix}
    Set Suite Variable    ${VM_OPT_OUT}        vm-dp-optout-${suffix}
    Set Suite Variable    ${VM_NODE_DRIVER}    vm-dp-nd-${suffix}
    Set up test environment
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    ...    storage_class=${IMAGE_STORAGE_CLASS}

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    # Always reset the setting and remove protection: a protected VM left behind
    # would block namespace cleanup on the test cluster.
    Run Keyword And Ignore Error    setting_keywords.reset    ${DEFAULT_SETTING}
    FOR    ${vm}    IN    ${VM_PROTECTED}    ${VM_CAPITAL}    ${VM_EXISTING}
    ...    ${VM_DEFAULTED}    ${VM_OPT_OUT}    ${VM_NODE_DRIVER}
        Unprotect And Delete VM    ${vm}
    END
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
