*** Settings ***
Documentation    Workload pod keywords - plain pods consuming PVCs, used for
...              data-integrity checks that need real IO on a volume.
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/workload_keywords.py


*** Keywords ***
Create Workload Pod With Volume
    [Arguments]    ${pod_name}    ${volume_name}    ${volume_mode}=Block    ${wait}=${True}
    workload_keywords.create_workload_pod    ${pod_name}    ${volume_name}    ${volume_mode}    ${wait}

Delete Workload Pod
    [Arguments]    ${pod_name}
    workload_keywords.delete_workload_pod    ${pod_name}

Write Block Pattern To Volume
    [Arguments]    ${pod_name}    ${size_mb}=128
    ${checksum}=    workload_keywords.write_block_pattern    ${pod_name}    ${size_mb}
    RETURN    ${checksum}

Overwrite Block Volume Head
    [Arguments]    ${pod_name}    ${size_mb}=8
    workload_keywords.overwrite_block_head    ${pod_name}    ${size_mb}

Block Volume Checksum
    [Arguments]    ${pod_name}    ${size_mb}=128
    ${checksum}=    workload_keywords.block_checksum    ${pod_name}    ${size_mb}
    RETURN    ${checksum}

Write File To Filesystem Volume
    [Arguments]    ${pod_name}    ${size_mb}=16
    ${checksum}=    workload_keywords.write_filesystem_file    ${pod_name}    ${size_mb}
    RETURN    ${checksum}

Filesystem Volume File Checksum
    [Arguments]    ${pod_name}
    ${checksum}=    workload_keywords.filesystem_file_checksum    ${pod_name}
    RETURN    ${checksum}

Filesystem Volume Capacity In MB
    [Arguments]    ${pod_name}
    ${capacity}=    workload_keywords.filesystem_capacity_mb    ${pod_name}
    RETURN    ${capacity}
