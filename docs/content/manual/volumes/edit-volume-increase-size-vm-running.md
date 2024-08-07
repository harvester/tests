---
title: Edit volume to increase size when vm is running
---
1. Create a VM
1. Make sure VM have started in running state with IP address
1. Open the `Edit config` page of the VM
1. Change the volume size of the disk on the Volumes page
1. Click Save
1. Check the prompt error message  
1. Open the Volumes page
1. Edit config of the volume attached to the VM
1. Change the volume size of the disk
1. Click Save
1. Check the prompt error message

## Expected Results
1. VM volume page should display error message
    ```
    admission webhook "validator.harvesterhci.io" denied the request: please stop the VM before resizing volumes
    ```
1. Volume page should display error message
    ```
    admission webhook "validator.harvesterhci.io" denied the request: resizing is only supported for detached volumes. The volume is being used by VM default/vm1. Please stop the VM first.
    ```