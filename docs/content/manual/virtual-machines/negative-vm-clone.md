---
title: Negative vm clone tests	
---

### Case 1 

1. Create a harvester cluster.
1. Create a VM `source-vm` with 3 volumes:
    * Image Volume
    * Volume
    * Container Volume
1. After VM starts, run command `echo "123" > test.txt && sync`.
1. Click `clone` button on the `source-vm` and input new VM name `target-vm`.
1. Delete `source-vm` while still cloning


#### Expected Results
- `target-vm` should finish cloning
- After cloning run command `cat ~/test.txt` in the `target-vm`. The result should be `123`.

### Case 2 

1. Create a harvester cluster.
1. Create a VM `source-vm` with 3 volumes:
    * Image Volume
    * Volume
    * Container Volume
1. After VM starts, run command `echo "123" > test.txt && sync`.
1. Click `clone` button on the `source-vm` and input new VM name `target-vm`.
1. Turn off node that has `source-vm` while cloning
1. Wait for clone to finish


#### Expected Results
- `target-vm` should finish cloning on node
- `source-vm` should have migrated to new node
- After cloning run command `cat ~/test.txt` in the `target-vm`. The result should be `123`.
