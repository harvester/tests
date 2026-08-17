*** Settings ***
Documentation    VM API Negative Test Cases
Test Tags        virtualmachines    negative    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/virtualmachine.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${IMG_NAME}         ${EMPTY}
# Outlandish value that no real cluster can ever satisfy
${MAX_RESOURCE}     999999
# Combinations of outlandish cpu/memory/disk requests, id-cpu-memory-disk_size
@{CASE_IDS}           cpu    mem    disk    mem-and-cpu    mem-cpu-and-disk
@{CASE_CPUS}          ${MAX_RESOURCE}    1    1    ${MAX_RESOURCE}    ${MAX_RESOURCE}
@{CASE_MEMORIES}      2Gi    ${MAX_RESOURCE}Gi    2Gi    ${MAX_RESOURCE}Gi    ${MAX_RESOURCE}Gi
@{CASE_DISK_SIZES}    10Gi    10Gi    ${MAX_RESOURCE}Gi    10Gi    ${MAX_RESOURCE}Gi


*** Test Cases ***
Get Non-Existent VM Returns Not Found
    [Tags]    p0
    [Documentation]    Getting a VM that does not exist must return 404 NotFound
    ${vm}=    Generate Unique Name    vm-missing
    ${result}=    Try To Get VM    ${vm}
    Operation Should Be Not Found    ${result}

Delete Non-Existent VM Returns Not Found
    [Tags]    p0
    [Documentation]    Deleting a VM that does not exist must return 404 NotFound
    ${vm}=    Generate Unique Name    vm-missing
    ${result}=    Try To Delete VM    ${vm}
    Operation Should Be Not Found    ${result}

Create VM With No Available Resources
    [Tags]    p0    sanity
    [Documentation]    Migrated from harvester_e2e_tests/integrations/test_3_vm_functions.py
    ...    test_create_vm_no_available_resources.
    ...
    ...    Requests outlandish CPU, memory, and/or disk (individually and
    ...    combined); each VM must be created (201) but remain
    ...    unschedulable, reporting both the GuestNotRunning and
    ...    Unschedulable condition reasons. Then delete it and verify it
    ...    (and its volumes) are gone.
    ...    Disk case is a known issue since v1.7.0:
    ...    https://github.com/harvester/harvester/issues/9850
    FOR    ${id}    ${cpu}    ${memory}    ${disk_size}    IN ZIP
    ...    ${CASE_IDS}    ${CASE_CPUS}    ${CASE_MEMORIES}    ${CASE_DISK_SIZES}
        ${vm}=    Generate Unique Name    vm-${id}
        VM is created    ${vm}    ${IMG_NAME}    cpu=${cpu}    memory=${memory}
        ...    disk_size=${disk_size}    requests_cpu=${cpu}    requests_memory=${memory}
        VM condition should be    ${vm}    GuestNotRunning    False    match_field=reason
        # Known issue since v1.7.0: oversized disk requests don't reliably
        # report Unschedulable. https://github.com/harvester/harvester/issues/9850
        IF    '${id}' not in ('disk', 'mem-cpu-and-disk')
            VM condition should be    ${vm}    Unschedulable    False    match_field=reason
        END
        VM is deleted    ${vm}
        VM should be deleted    ${vm}
    END


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}    img-${suffix}
    Set up test environment
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    Run Keyword If All Tests Passed    Delete Suite Resources

Delete Suite Resources
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
