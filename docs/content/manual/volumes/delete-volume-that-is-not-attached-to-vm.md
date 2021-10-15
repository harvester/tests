---
title: Delete volume that is not attached to a VM
---
1. Create volume
1. Validate that it created
1. Check the volume crd.
1. Delete the volume
1. Verify that volume is removed from list
1. Check the volume object doesn't exist anymore.

## Expected Results
1. Volume should create
1. It should show in volume list
1. Volume crd should have correct info.
1. Volume should delete.
1. Volume should be removed from list