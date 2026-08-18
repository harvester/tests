*** Settings ***
Documentation    GPU Operator Test Cases
...             Installs the NVIDIA GPU Operator via a HelmChart CR, discovers
...             GPU-equipped nodes, and validates a CUDA workload.
...
...             Skip conditions (checked in Suite Setup):
...               - pcidevices-controller addon is already enabled
...               - nvidia-driver-toolkit addon is already enabled
...             In either case the suite is skipped to avoid addon conflicts.
...
...             When no GPU nodes are found after installation, the test emits
...             a WARN-level message but still passes; the CUDA workload step
...             is skipped via Pass Execution If.
Test Tags        regression    gpu-operator

Resource         ../../../keywords/variables.resource
Resource         ../../../keywords/common.resource
Resource         ../../../keywords/helmchart.resource
Resource         ../../../keywords/pod.resource
Resource         ../../../keywords/gpu_operator.resource

Suite Setup      GPU Operator Suite Setup
Suite Teardown   GPU Operator Suite Teardown
Test Teardown    Common Test Teardown


*** Variables ***
${GPU_OPERATOR_NAME}       gpu-operator
${KUBE_SYSTEM_NS}          kube-system
${GPU_OPERATOR_NS}         gpu-operator
${CUDA_POD_NAME}           cuda-vectoradd
${CUDA_POD_NS}             default
${GPU_LABEL_KEY}           harvesterhci.io/gpu-baremetal-workloads
${GPU_LABEL_VALUE}         true
${ADDON_PCIDEVICES}        pcidevices-controller
${ADDON_NVIDIA_TOOLKIT}    nvidia-driver-toolkit
${GPU_OPERATOR_TIMEOUT}    1800
# Observed pod-ready time on tested hardware: ~2 min. 300 s (~5 min, ≈2.5×) gives a safe margin.
${GPU_OPERATOR_PODS_TIMEOUT}    300
${CUDA_POD_TIMEOUT}        300
# Set at runtime
${GPU_NODES}               ${EMPTY}


*** Test Cases ***
Test GPU Operator Helm Installation
    [Tags]    p0    coretest    gpu-operator
    [Documentation]    Install GPU operator via HelmChart CRD and wait for deployment.
    ...               Steps:
    ...                   1. Add harvesterhci.io/gpu-baremetal-workloads=true to every node
    ...                   2. Create the gpu-operator HelmChart CR in kube-system
    ...                   3. Wait for the HelmChart install job to complete
    ...               Expected Result:
    ...                   - All non-witness nodes carry the baremetal-workloads label
    ...                   - HelmChart install job finishes with status Complete

    # Step 1: Label every non-witness node
    Given All Nodes Are Labeled For GPU Baremetal Workloads

    # Step 2: Create HelmChart CR
    When GPU Operator HelmChart Is Created

    # Step 3: Wait for successful deployment
    Then GPU Operator Should Be Deployed

    # Step 4: Confirm all operator pods are Running/Completed
    And GPU Operator Pods Should Be Running

Test GPU Node Discovery And CUDA Validation
    [Tags]    p1    gpu-operator    cuda
    [Documentation]    Discover GPU nodes; if any are present, run a CUDA workload.
    ...               When no GPU nodes are found the test emits a WARNING and
    ...               passes without running the CUDA pod (environment may not
    ...               have GPU hardware).
    ...               Steps:
    ...                   1. Inspect every node's allocatable nvidia.com/gpu resource
    ...                   2. Warn and skip CUDA steps if no GPU nodes detected
    ...                   3. Create cuda-vectoradd pod requesting one GPU
    ...                   4. Wait for the pod to reach Succeeded phase
    ...                   5. Verify the expected "Test PASSED" output in pod logs
    ...               Expected Result:
    ...                   - GPU nodes logged (or WARNING if none)
    ...                   - CUDA vectoradd reports "Test PASSED" when GPU is present

    # Step 1: Discover GPU nodes
    ${gpu_nodes}=    Discover GPU Nodes
    Set Suite Variable    ${GPU_NODES}    ${gpu_nodes}

    # Step 2: Warn and skip CUDA if no GPU hardware is present
    ${gpu_count}=    Get Length    ${gpu_nodes}
    Run Keyword If    ${gpu_count} == 0
    ...    Log    WARNING: No GPU nodes found in this cluster - CUDA workload test will be skipped    WARN
    Pass Execution If    ${gpu_count} == 0
    ...    No GPU nodes detected; skipping CUDA workload validation

    # Steps 3-5: CUDA workload validation (reached only when GPU nodes exist)
    When CUDA Vectoradd Pod Is Created
    Then CUDA Pod Should Succeed
    And CUDA Output Should Be Correct


*** Keywords ***
GPU Operator Suite Setup
    [Documentation]    Initialise the test environment and skip if conflicting addons
    ...               are already enabled.
    Log    Initialising GPU operator test environment
    Set up test environment
    ${conflict}=    gpu_operator_keywords.Check Conflicting Addons
    ...    ${ADDON_PCIDEVICES}    ${ADDON_NVIDIA_TOOLKIT}
    Run Keyword If    ${conflict}
    ...    Skip
    ...    pcidevices-controller or nvidia-driver-toolkit addon is already enabled - skipping GPU operator suite to avoid conflicts
    Log    No conflicting addons detected; proceeding with GPU operator tests

GPU Operator Suite Teardown
    [Documentation]    Clean up all resources created by this suite.
    ...               Node labels and HelmChart are always removed; errors are
    ...               ignored so that all cleanup steps run regardless.
    Log    Running GPU operator suite teardown
    Run Keyword And Ignore Error
    ...    Delete Pod If Exists    ${CUDA_POD_NAME}    ${CUDA_POD_NS}
    Run Keyword And Ignore Error
    ...    Delete HelmChart    ${GPU_OPERATOR_NAME}    ${KUBE_SYSTEM_NS}
    Run Keyword And Ignore Error
    ...    gpu_operator_keywords.Remove Gpu Baremetal Label From All Nodes    ${GPU_LABEL_KEY}
    Cleanup test resources
    Log    GPU operator suite teardown completed
