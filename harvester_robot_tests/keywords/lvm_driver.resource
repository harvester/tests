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

Create LVM Encryption Secret
    [Arguments]    ${name}    ${passphrase}
    lvm_driver_keywords.create_encryption_secret    ${name}    ${passphrase}

Delete Secret
    [Arguments]    ${name}
    lvm_driver_keywords.delete_secret    ${name}

Try To Delete Secret
    [Arguments]    ${name}
    ${result}=    lvm_driver_keywords.try_delete_secret    ${name}
    RETURN    ${result}

Secret Should Exist
    [Arguments]    ${name}
    ${exists}=    lvm_driver_keywords.secret_exists    ${name}
    Should Be True    ${exists}    msg=Secret ${name} does not exist

Get LVM Volume Handle
    [Arguments]    ${pvc_name}
    ${handle}=    lvm_driver_keywords.get_volume_handle    ${pvc_name}
    RETURN    ${handle}

LVM Volume Should Be Encrypted With LUKS2
    [Arguments]    ${node}    ${vg}    ${pvc_name}
    [Documentation]    The backing LV of the PVC carries a LUKS2 header and is
    ...    open on the node as the dm-crypt mapping csi-lvm-<volume id>.
    ${handle}=    Get LVM Volume Handle    ${pvc_name}
    lvm_driver_keywords.lv_should_be_luks2    ${node}    ${vg}    ${handle}
    lvm_driver_keywords.crypt_mapping_should_be_active    ${node}    ${vg}    ${handle}

Plaintext Should Not Reach The Backing LV
    [Arguments]    ${node}    ${vg}    ${pvc_name}    ${marker}    ${size_mb}=32
    [Documentation]    The marker the consumer wrote must not appear in the raw
    ...    LV: the data is only stored as ciphertext.
    ${handle}=    Get LVM Volume Handle    ${pvc_name}
    ${count}=    lvm_driver_keywords.raw_lv_marker_count    ${node}    ${vg}    ${handle}
    ...    ${marker}    ${size_mb}
    Should Be Equal As Integers    ${count}    0
    ...    msg=Plaintext marker found ${count} times on /dev/${vg}/${handle}: the volume is not encrypted at rest
