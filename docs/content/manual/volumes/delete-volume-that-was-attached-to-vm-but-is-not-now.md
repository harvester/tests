---
title: Delete volume that was attached to VM but now is not (e2e_be_fe)
---
1. Create a VM with a root volume
1. Write 10Gi data into it.
1. Delete the VM but not the volume
1. Verify Volume still exists
1. Check disk space on node
1. Delete the volume
1. Verify that volume is removed from list
1. Check disk space on node

## Expected Results
1. VM should create
1. 10Gi space should be consumed on the disk.
1. VM should delete
1. Volume should still show in Volume list
1. Disk space should show 10Gi + 
1. Volume should delete
1. Volume should be removed from list
1. Space should be less than before
