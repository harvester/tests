*** Settings ***
Documentation    GPU Operator Keywords
Resource         variables.resource
Resource         common.resource
Resource         helmchart.resource
Resource         pod.resource
Library          ../libs/keywords/gpu_operator_keywords.py

*** Keywords ***
All Nodes Are Labeled For GPU Baremetal Workloads
    [Documentation]    Patch every non-witness node with the gpu-baremetal-workloads label.
    ${labeled}=    gpu_operator_keywords.Add Gpu Baremetal Label To All Nodes
    ...    ${GPU_LABEL_KEY}    ${GPU_LABEL_VALUE}
    Log    Labeled ${labeled} node(s) with ${GPU_LABEL_KEY}=${GPU_LABEL_VALUE}

GPU Operator HelmChart Is Created
    [Documentation]    Create the GPU operator HelmChart CR in kube-system.
    Create GPU Operator HelmChart    ${GPU_OPERATOR_NAME}    ${KUBE_SYSTEM_NS}    ${GPU_OPERATOR_NS}
    Log    HelmChart '${GPU_OPERATOR_NAME}' created in namespace '${KUBE_SYSTEM_NS}'

GPU Operator Should Be Deployed
    [Documentation]    Wait for the HelmChart install job to report Complete.
    Wait For HelmChart Deployed    ${GPU_OPERATOR_NAME}    ${KUBE_SYSTEM_NS}    ${GPU_OPERATOR_TIMEOUT}
    Log    GPU operator HelmChart deployed successfully

GPU Operator Pods Should Be Running
    [Documentation]    Poll the gpu-operator namespace until all pods are Running or Completed.
    ...               Minimum 4 pods are expected (base install without GPU hardware).
    ...               With GPU hardware additional nvidia-* daemonset pods also appear.
    gpu_operator_keywords.Wait For Gpu Operator Pods Ready
    ...    ${GPU_OPERATOR_NS}    ${GPU_OPERATOR_PODS_TIMEOUT}
    Log    All GPU operator pods are ready in namespace '${GPU_OPERATOR_NS}'

Discover GPU Nodes
    [Documentation]    Return list of nodes that expose nvidia.com/gpu allocatable.
    ${nodes}=    gpu_operator_keywords.Get Nodes With Gpu
    ${count}=    Get Length    ${nodes}
    Log    Found ${count} GPU node(s): ${nodes}
    RETURN    ${nodes}

CUDA Vectoradd Pod Is Created
    [Documentation]    Create the cuda-vectoradd sample pod requesting one GPU.
    gpu_operator_keywords.Create Cuda Vectoradd Pod    ${CUDA_POD_NAME}    ${CUDA_POD_NS}
    Log    Pod '${CUDA_POD_NAME}' created in namespace '${CUDA_POD_NS}'

CUDA Pod Should Succeed
    [Documentation]    Wait for the cuda-vectoradd pod to reach Succeeded phase.
    Wait For Pod Succeeded    ${CUDA_POD_NAME}    ${CUDA_POD_NS}    ${CUDA_POD_TIMEOUT}
    Log    Pod '${CUDA_POD_NAME}' reached Succeeded phase

CUDA Output Should Be Correct
    [Documentation]    Read pod logs and assert the expected "Test PASSED" output.
    ${logs}=    Get Pod Logs    ${CUDA_POD_NAME}    ${CUDA_POD_NS}
    gpu_operator_keywords.Verify Cuda Output    ${logs}
    Log    CUDA vectoradd output verified
