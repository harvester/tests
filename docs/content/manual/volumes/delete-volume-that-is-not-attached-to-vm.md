---
title: Delete volume that is not attached to a VM (e2e_be_fe)
---
1. Create volume
1. Validate that it created
1. Check the volume crd.
1. Delete the volume
1. Verify that volume is removed from list
1. Check the volume object doesn't exist anymore.

1. Create a VM
1. Make sure VM have started in running state with IP address
1. Delete the VM 
1. Do not select the option `Select the volume you want to delete` (Keep volume)
1. Click the Delete button
1. Open Volumes page
1. Delete the volume remains for the VM 

## Expected Results
1. Volume should create
1. It should show in volume list
1. Volume crd should have correct info.
1. Volume should delete.
1. Volume should be removed from list

1. VM should be removed correctly
1. The remains volume can also be deleted on volumes page
