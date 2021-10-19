---
title: Power down the node	
---
1. Create two vms on a cluster.
2. Power down the node.
3. Try to migrate a VM from the down node to active node.
4. Leave the 2nd vm as it is.

## Expected Results
1. The 1st VM should be migrated to other node on manually doing it.
2. The 2nd VM should be recovered from the lost node