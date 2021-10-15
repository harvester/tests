---
title: Negative node unschedulable during live migration	
---
## Prerequisite: 
1. Cluster is of 3 nodes.
1. VM is running on Node-1
1. Node-2 and Node-3 don't have space to migrate a VM to them.

## Steps:
1. Create a vm on node-1
2. Migrate the VM.

## Expected Results
1. Migration should not be started.
1. Relevant error should be shown on the GUI.
1. The existing VM should be accessible and the health check of the VM should be fine