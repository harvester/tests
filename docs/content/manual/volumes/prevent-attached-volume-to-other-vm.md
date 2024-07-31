---
title: A volume can't be attached to another VM (Yaml)
---

* Related issues: [#5383](https://github.com/harvester/harvester/issues/5383) [ENHANCEMENT] Refactor harvesterhci.io/owned-by annotation on PVC

## Category: 
* Volume

## Verification Steps
1. Create two VMs (vm1 and vm2)
1. Create a data volume `vol-001`
1. Click the `add volume` menu option for `vm1` to attach `vol-001` to vm1
1. Ensure `vol-001` can correctly been attached to `vm1`
1. Click the `add volume` menu option for `vm2` and find available volume

1. Edit the yaml of vm2
1. Try to attach the data volume yaml content from vm1 to vm2 spec.volume
```
        - name: data-vol
          persistentVolumeClaim:
            claimName: vol-001
            hotpluggable: true
```
1. Click Save 
1. Check the failure message prompt

## Expected Results
1. No volume can't be found in the list when click the `add volume` menu option for `vm2`
1. Should prompt the error message to prevent 
    ```
    admission webhook "validator.harvesterhci.io" denied the request: the volume vol-001 is already used by VM default/vm1
    ```
    {{< image "images/volumes/5383-image-01.png" >}}