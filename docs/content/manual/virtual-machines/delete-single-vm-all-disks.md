---
title: Delete single vm all disks (e2e_be)
---
1. Create a VM
1. Make sure VM have started in running state with IP address
1. Delete the VM
1. Select the option `Select the volume you want to delete` (delete volume)

## Expected Results
1. You should check amount of used space on Server before you delete the VM
1. VM should be deleted
1. It should not show up in the Virtual Machine list
1. All volumes attached to the VM should be deleted on the volume page
1. Verify the cleaned up the space on the disk on the node.
