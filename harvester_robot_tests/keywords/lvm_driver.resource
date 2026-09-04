*** Settings ***
Documentation    LVM driver internals - snapshot handles, location records,
...              backend LV checks on nodes, pre-provisioned snapshot import.
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/lvm_driver_keywords.py


*** Keywords ***
Configure LVM Snapshot Class In CSI Driver Config
    lvm_driver_keywords.ensure_csi_driver_config

Remove LVM Snapshot Class From CSI Driver Config
    lvm_driver_keywords.remove_csi_driver_config

Get Snapshot Handle
    [Arguments]    ${snapshot_name}
    ${handle}=    lvm_driver_keywords.get_snapshot_handle    ${snapshot_name}
    RETURN    ${handle}

Snapshot Location Record Should Exist
    [Arguments]    ${snapshot_handle}    ${node}    ${vg}
    lvm_driver_keywords.location_record_should_exist    ${snapshot_handle}    ${node}    ${vg}

Snapshot Location Record Should Not Exist
    [Arguments]    ${snapshot_handle}
    lvm_driver_keywords.location_record_should_not_exist    ${snapshot_handle}

Snapshot LV Should Exist On Node
    [Arguments]    ${node}    ${vg}    ${snapshot_handle}
    lvm_driver_keywords.snapshot_lv_should_exist    ${node}    ${vg}    ${snapshot_handle}

Snapshot LV Should Not Exist On Node
    [Arguments]    ${node}    ${vg}    ${snapshot_handle}
    lvm_driver_keywords.snapshot_lv_should_not_exist    ${node}    ${vg}    ${snapshot_handle}

No LVM Helper Pods Should Remain
    lvm_driver_keywords.no_helper_pods_should_remain

No PV Should Reference Claim
    [Arguments]    ${pvc_name}
    lvm_driver_keywords.no_pv_should_reference_claim    ${pvc_name}

Create Retain Volume Snapshot Class
    [Arguments]    ${class_name}
    lvm_driver_keywords.create_retain_snapshot_class    ${class_name}

Delete Volume Snapshot Class
    [Arguments]    ${class_name}
    lvm_driver_keywords.delete_snapshot_class    ${class_name}

Release Snapshot Keeping Backend LV
    [Arguments]    ${snapshot_name}
    ${handle}=    lvm_driver_keywords.release_snapshot_keeping_backend    ${snapshot_name}
    RETURN    ${handle}

Import Pre-Provisioned Snapshot
    [Arguments]    ${snapshot_name}    ${snapshot_handle}    ${size}
    lvm_driver_keywords.import_preprovisioned_snapshot    ${snapshot_name}    ${snapshot_handle}    ${size}

Delete Imported Snapshot And Wait For Backend Cleanup
    [Arguments]    ${snapshot_name}
    lvm_driver_keywords.delete_imported_snapshot    ${snapshot_name}
