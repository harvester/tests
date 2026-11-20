*** Settings ***
Documentation    Assertions for VMImage deletion protection (harvester/harvester#12011).
Resource         image.resource
Resource         virtualmachine.resource
Resource         volume.resource


*** Keywords ***
Set Up CDI Test Environment
    [Documentation]    Initialize Kubernetes for the CRD-only CDI deletion tests.
    common_keywords.init k8s api client

Image Deletion Should Be Blocked
    [Arguments]    ${image_name}    ${consumer}
    ${result}=    Try To Delete Image    ${image_name}
    Operation Should Be Rejected    ${result}
    Should Be Equal As Integers    ${result}[code]    409
    Should Contain    ${result}[message]    ${consumer}
    ${metadata}=    image_keywords.get_image_metadata    ${image_name}
    ${deleting}=    Evaluate    $metadata.get('deletionTimestamp')
    Should Be Equal    ${deleting}    ${NONE}

Get PVC Identity
    [Arguments]    ${pvc_name}
    ${metadata}=    volume_keywords.get_volume_metadata    ${pvc_name}
    Should Not Be Empty    ${metadata}[uid]
    RETURN    ${metadata}[uid]

PVC Should Be Retained
    [Arguments]    ${pvc_name}    ${uid}
    ${metadata}=    volume_keywords.get_volume_metadata    ${pvc_name}
    Should Be Equal    ${metadata}[uid]    ${uid}
    Should Be Equal    ${metadata}[deletionTimestamp]    ${NONE}
    Volume Phase Is Bound    ${pvc_name}

DataVolume Should Be Complete
    [Arguments]    ${pvc_name}
    ${dv}=    volume_keywords.get_data_volume    ${pvc_name}
    Should Be Equal    ${dv}[status][phase]    Succeeded
    ${deleting}=    Evaluate    $dv['metadata'].get('deletionTimestamp')
    Should Be Equal    ${deleting}    ${NONE}
    RETURN    ${dv}

Clone Should Be Complete
    [Arguments]    ${pvc_name}    ${image_name}
    ${dv}=    DataVolume Should Be Complete    ${pvc_name}
    Should Be Equal    ${dv}[spec][source][pvc][namespace]    ${DEFAULT_NAMESPACE}
    Should Be Equal    ${dv}[spec][source][pvc][name]    ${image_name}
    ${claim}=    Evaluate    $dv['status'].get('claimName') or $dv['metadata']['name']
    Should Be Equal    ${claim}    ${pvc_name}
    Should Not Be Equal    ${pvc_name}    ${image_name}

VM Should Use Only PVC
    [Arguments]    ${vm_name}    ${pvc_name}
    ${claims}=    Get VM Volumes    ${vm_name}
    ${expected}=    Create List    ${pvc_name}
    Lists Should Be Equal    ${claims}    ${expected}

VM Should Use Golden PVC
    [Arguments]    ${vm_name}    ${image_name}
    VM Should Use Only PVC    ${vm_name}    ${image_name}
    ${metadata}=    volume_keywords.get_volume_metadata    ${image_name}
    Should Be Equal    ${metadata}[annotations][harvesterhci.io/goldenImage]    true
    ${result}=    Try Get Vm    ${vm_name}
    Should Be True    ${result}[success]
    ${vm}=    Set Variable    ${result}[message]
    Should Be Equal    ${vm}[metadata][labels][migration.harvesterhci.io/imported]    true
    Should Be Equal    ${vm}[metadata][annotations][harvesterhci.io/volumeClaimTemplates]    []

Delete Unused Image
    [Arguments]    ${image_name}
    [Documentation]    Allow the webhook caches to observe removal of the image's consumers.
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Delete image by name    ${image_name}
    Wait for image deleted by name    ${image_name}
    Wait Until Volume Is Deleted    ${image_name}
