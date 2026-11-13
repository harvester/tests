*** Settings ***
Documentation    Terraform Keywords
...    Resources managed through the Harvester terraform provider. See
...    libs/terraform/terraform.py for the environment variables that select
...    the terraform binary and the provider version.
Library          ../libs/keywords/terraform_keywords.py
Resource         variables.resource


*** Keywords ***
Terraform workspace is initialized
    [Arguments]    ${workspace}
    [Documentation]    Create an empty configuration and install the provider
    terraform_keywords.init workspace    ${workspace}

Terraform VM is defined
    [Arguments]    ${workspace}    ${vm_name}    ${image_name}    ${namespace}=${DEFAULT_NAMESPACE}
    ...    ${cpu}=1    ${memory}=1Gi    ${disk_size}=${DEFAULT_VOLUME_SIZE}
    [Documentation]    Add a VM booting from the image, on the management network
    terraform_keywords.add virtual machine    ${workspace}    ${vm_name}
    ...    ${DEFAULT_NAMESPACE}/${image_name}    ${namespace}    ${cpu}    ${memory}    ${disk_size}

Terraform VM requires node label
    [Arguments]    ${workspace}    ${vm_name}    ${key}    ${value}
    [Documentation]    Required node affinity: only nodes labelled key=value
    terraform_keywords.set required node affinity    ${workspace}    ${vm_name}    ${key}    ${value}

Terraform VM avoids VMs
    [Arguments]    ${workspace}    ${vm_name}    @{other_vm_names}
    [Documentation]    Required pod anti-affinity: never on a node running the other VMs
    terraform_keywords.set required pod anti affinity    ${workspace}    ${vm_name}    @{other_vm_names}

Terraform configuration is applied
    [Arguments]    ${workspace}
    terraform_keywords.apply    ${workspace}

Terraform plan should have no changes
    [Arguments]    ${workspace}
    [Documentation]    The provider reads back what it applied (no perpetual diff)
    ${changes}=    terraform_keywords.plan has changes    ${workspace}
    Should Not Be True    ${changes}    msg=terraform plan shows changes right after apply

Terraform workspace is destroyed
    [Arguments]    ${workspace}
    terraform_keywords.destroy    ${workspace}
