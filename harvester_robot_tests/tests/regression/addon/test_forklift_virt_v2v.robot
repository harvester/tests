*** Settings ***
Documentation    Forklift virt-v2v image for Windows and SLES guests
...    (harvester/forklift-packaging#24; harvester/harvester#11657, #11775,
...    #11851). The SUSE VM Migration Toolkit converts every guest with the
...    virt-v2v image configured on the forklift-controller. The image must
...    carry a virt-v2v that inspects Windows Server 2022 (>= 2.11), the
...    Windows firstboot tools (rhsrvany.exe, pnp_wait.exe) and virtio-win,
...    a libvirt with the vpx driver, the perl-Bootloader fallback for SLES 15,
...    and a libguestfs appliance that boots with the inspection tools.
...    The image cases run the configured image as an idle pod and need no
...    source hypervisor. The migration cases need a vSphere Provider, storage
...    and network maps and source VMs, passed through the FORKLIFT_* variables
...    below; they are skipped when those are unset.
Test Tags        regression    addon    forklift    vm-import

Resource         ../../../keywords/variables.resource
Resource         ../../../keywords/common.resource
Resource         ../../../keywords/forklift.resource
Resource         ../../../keywords/virtualmachine.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown
Test Teardown    Common Test Teardown


*** Variables ***
# Cold migration sources (all must be set for the migration cases)
${FORKLIFT_SOURCE_PROVIDER}     %{FORKLIFT_SOURCE_PROVIDER=}
${FORKLIFT_STORAGE_MAP}         %{FORKLIFT_STORAGE_MAP=}
${FORKLIFT_NETWORK_MAP}         %{FORKLIFT_NETWORK_MAP=}
# Source VM names in the provider inventory; shut the Windows source down
# cleanly first (a dirty NTFS cannot be converted).
${FORKLIFT_WINDOWS_VM}          %{FORKLIFT_WINDOWS_VM=}
${FORKLIFT_SLES_VM}             %{FORKLIFT_SLES_VM=}
# virt-v2v image to inspect; empty uses the image the forklift-controller is
# configured with (set it to validate a candidate image before rolling it out)
${VIRT_V2V_IMAGE}               %{VIRT_V2V_IMAGE=}
${MIGRATION_TIMEOUT}            %{FORKLIFT_MIGRATION_TIMEOUT=7200}
${AGENT_TIMEOUT}                1800
${NAME_PREFIX}                  %{NAME_PREFIX=forklift}

# Dynamic Variables
${PROBE_POD}                    ${EMPTY}
${WINDOWS_PLAN}                 ${EMPTY}
${SLES_PLAN}                    ${EMPTY}
${WINDOWS_TARGET_VM}            ${EMPTY}
${SLES_TARGET_VM}               ${EMPTY}


*** Test Cases ***
virt-v2v Inspects Windows Server 2022
    [Tags]    p0    windows
    [Documentation]    harvester/harvester#11657: virt-v2v 2.7.7 aborts Windows
    ...    Server 2022 inspection with Hivex.Error. The image must ship 2.11 or
    ...    newer, with the vCenter input path.
    virt-v2v Version Should Be At Least    ${PROBE_POD}    2.11
    virt-v2v Should Support    ${PROBE_POD}    vcenter-https    input:libvirt    output:kubevirt
    libvirt Should Have The vpx Driver    ${PROBE_POD}

virt-v2v Ships The Windows Firstboot Tools
    [Tags]    p0    windows
    [Documentation]    harvester/harvester#11775: without rhsrvany.exe and
    ...    pnp_wait.exe virt-v2v cannot install the firstboot service that
    ...    installs the virtio drivers and the guest agent in Windows guests.
    Files Should Exist In virt-v2v Image    ${PROBE_POD}
    ...    /usr/share/virt-tools/rhsrvany.exe    /usr/share/virt-tools/pnp_wait.exe
    Directory Should Not Be Empty In virt-v2v Image    ${PROBE_POD}    /usr/share/virtio-win

virt-v2v Tolerates perl-Bootloader Failures On SLES Guests
    [Tags]    p0    sles
    [Documentation]    harvester/harvester#11851: SLES 15 SP5 conversions abort
    ...    with "no $default->{image}" because a perl-Bootloader failure is
    ...    fatal. The image must carry the fallback that turns it into a
    ...    warning (libguestfs/libguestfs-common#56).
    virt-v2v Should Tolerate perl-Bootloader Failures    ${PROBE_POD}

libguestfs Appliance Boots With The Inspection Tools
    [Tags]    p1
    [Documentation]    supermin builds the appliance from the image's packages;
    ...    a trimmed package set boots but fails inspection with
    ...    "execvp: file: No such file or directory".
    libguestfs Appliance Should Boot With Inspection Tools    ${PROBE_POD}

Migrated Windows Server VM Boots With Guest Agent
    [Tags]    p0    windows    migration
    [Documentation]    Cold-migrate a Windows Server source VM. The migrated VM
    ...    must boot and its guest agent - installed by the virt-v2v firstboot
    ...    service - must connect.
    Migration Sources Should Be Configured    ${FORKLIFT_WINDOWS_VM}
    ${vm}=    VM Is Migrated From Provider    ${WINDOWS_PLAN}    ${FORKLIFT_SOURCE_PROVIDER}
    ...    ${FORKLIFT_STORAGE_MAP}    ${FORKLIFT_NETWORK_MAP}    ${FORKLIFT_WINDOWS_VM}
    ...    timeout=${MIGRATION_TIMEOUT}
    Set Suite Variable    ${WINDOWS_TARGET_VM}    ${vm}
    Migrated VM Should Boot With Guest Agent    ${vm}

Migrated SLES VM Boots With Guest Agent
    [Tags]    p0    sles    migration
    [Documentation]    Cold-migrate a SLES 15 source VM. Conversion must finish
    ...    despite the perl-Bootloader failure, and the VM must boot, get an IP
    ...    address and connect the guest agent installed at firstboot.
    Migration Sources Should Be Configured    ${FORKLIFT_SLES_VM}
    ${vm}=    VM Is Migrated From Provider    ${SLES_PLAN}    ${FORKLIFT_SOURCE_PROVIDER}
    ...    ${FORKLIFT_STORAGE_MAP}    ${FORKLIFT_NETWORK_MAP}    ${FORKLIFT_SLES_VM}
    ...    timeout=${MIGRATION_TIMEOUT}
    Set Suite Variable    ${SLES_TARGET_VM}    ${vm}
    Migrated VM Should Boot With Guest Agent    ${vm}


*** Keywords ***
Local Suite Setup
    Set up test environment
    Forklift Addon Should Be Enabled
    ${suffix}=    Generate Unique Name    ${NAME_PREFIX}
    Set Suite Variable    ${PROBE_POD}       v2v-probe-${suffix}
    Set Suite Variable    ${WINDOWS_PLAN}    win-${suffix}
    Set Suite Variable    ${SLES_PLAN}       sles-${suffix}
    ${image}=    Start virt-v2v Image Probe    ${PROBE_POD}    ${VIRT_V2V_IMAGE}
    Log    Inspecting virt-v2v image ${image}    console=yes

Migration Sources Should Be Configured
    [Arguments]    ${source_vm}
    Skip If    not ("${FORKLIFT_SOURCE_PROVIDER}" and "${FORKLIFT_STORAGE_MAP}" and "${FORKLIFT_NETWORK_MAP}" and "${source_vm}")
    ...    Set FORKLIFT_SOURCE_PROVIDER, FORKLIFT_STORAGE_MAP, FORKLIFT_NETWORK_MAP and the source VM to run migrations
    Forklift Provider Should Be Ready    ${FORKLIFT_SOURCE_PROVIDER}

Migrated VM Should Boot With Guest Agent
    [Arguments]    ${vm}
    # Forklift keeps the source power state; start the VM if it came up off
    Run Keyword And Ignore Error    VM is started    ${vm}
    VM should be running    ${vm}
    VM should have IP addresses    ${vm}
    VM qemu-agent should be connected    ${vm}    timeout=${AGENT_TIMEOUT}

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    Run Keyword And Ignore Error    Stop virt-v2v Image Probe    ${PROBE_POD}
    IF    "${WINDOWS_TARGET_VM}"
        Run Keyword And Ignore Error    VM is deleted    ${WINDOWS_TARGET_VM}
    END
    IF    "${SLES_TARGET_VM}"
        Run Keyword And Ignore Error    VM is deleted    ${SLES_TARGET_VM}
    END
    IF    "${WINDOWS_PLAN}"
        Run Keyword And Ignore Error    Migration Plan Is Deleted    ${WINDOWS_PLAN}
    END
    IF    "${SLES_PLAN}"
        Run Keyword And Ignore Error    Migration Plan Is Deleted    ${SLES_PLAN}
    END
