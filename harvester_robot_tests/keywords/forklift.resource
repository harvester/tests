*** Settings ***
Documentation    Forklift (SUSE VM Migration Toolkit addon) Keywords - the
...              virt-v2v conversion image and cold migrations from vSphere.
Library          ../libs/keywords/forklift_keywords.py
Library          ../libs/keywords/addon_keywords.py
Resource         variables.resource
Resource         common.resource


*** Variables ***
${FORKLIFT_ADDON_NAME}      forklift-operator


*** Keywords ***
Forklift Addon Should Be Enabled
    [Documentation]    Skip the calling suite when the forklift-operator addon is
    ...    not enabled; the suite never enables addons on its own.
    ${enabled}=    addon_keywords.is_addon_enabled    ${FORKLIFT_ADDON_NAME}
    Skip If    not ${enabled}    The ${FORKLIFT_ADDON_NAME} addon is not enabled on this cluster

Start virt-v2v Image Probe
    [Arguments]    ${pod_name}    ${image}=${EMPTY}
    [Documentation]    Run a virt-v2v image as an idle pod, to inspect it. An
    ...    empty image means the one Forklift is configured with. Returns the
    ...    image reference.
    ${image}=    forklift_keywords.start_virt_v2v_probe    ${pod_name}    ${image}
    RETURN    ${image}

Stop virt-v2v Image Probe
    [Arguments]    ${pod_name}
    forklift_keywords.stop_virt_v2v_probe    ${pod_name}

virt-v2v Version Should Be At Least
    [Arguments]    ${pod_name}    ${minimum}
    ${version}=    forklift_keywords.virt_v2v_version_should_be_at_least    ${pod_name}    ${minimum}
    RETURN    ${version}

virt-v2v Should Support
    [Arguments]    ${pod_name}    @{features}
    forklift_keywords.virt_v2v_should_support_features    ${pod_name}    @{features}

libvirt Should Have The vpx Driver
    [Arguments]    ${pod_name}
    forklift_keywords.libvirt_should_have_vpx_driver    ${pod_name}

Files Should Exist In virt-v2v Image
    [Arguments]    ${pod_name}    @{paths}
    forklift_keywords.files_should_exist_in_image    ${pod_name}    @{paths}

Directory Should Not Be Empty In virt-v2v Image
    [Arguments]    ${pod_name}    ${path}
    forklift_keywords.directory_should_not_be_empty_in_image    ${pod_name}    ${path}

virt-v2v Should Tolerate perl-Bootloader Failures
    [Arguments]    ${pod_name}
    forklift_keywords.virt_v2v_should_tolerate_perl_bootloader_failures    ${pod_name}

libguestfs Appliance Should Boot With Inspection Tools
    [Arguments]    ${pod_name}
    forklift_keywords.libguestfs_appliance_should_boot_with_inspection_tools    ${pod_name}

Forklift Provider Should Be Ready
    [Arguments]    ${name}
    forklift_keywords.provider_should_be_ready    ${name}

VM Is Migrated From Provider
    [Arguments]    ${plan_name}    ${source_provider}    ${storage_map}    ${network_map}
    ...    ${source_vm}    ${target_namespace}=${DEFAULT_NAMESPACE}    ${timeout}=7200
    [Documentation]    Cold-migrate one source VM with a new Plan and Migration
    ...    and wait for it to succeed. Returns the name of the migrated VM.
    forklift_keywords.create_migration_plan    ${plan_name}    ${source_provider}
    ...    ${storage_map}    ${network_map}    ${source_vm}    ${target_namespace}
    forklift_keywords.wait_for_plan_ready    ${plan_name}
    forklift_keywords.start_migration    ${plan_name}    ${plan_name}
    forklift_keywords.wait_for_migration_succeeded    ${plan_name}    ${timeout}
    ${vm}=    forklift_keywords.get_migrated_vm_name    ${plan_name}    ${source_vm}
    RETURN    ${vm}

Migration Plan Is Deleted
    [Arguments]    ${plan_name}    ${target_namespace}=${DEFAULT_NAMESPACE}
    [Documentation]    Delete the Migration and Plan (both named ${plan_name})
    ...    and the volumes Forklift created for the plan.
    forklift_keywords.delete_migration_plan    ${plan_name}    ${plan_name}    ${target_namespace}
