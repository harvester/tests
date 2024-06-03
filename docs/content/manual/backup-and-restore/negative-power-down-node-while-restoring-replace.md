---
title: Negative Power down the node where the VM is getting replaced by the restore
---

* Related issues
    - [tests#1263](https://github.com/harvester/tests/issues/1263) [ReleaseTesting] Negative Power down the node where the VM is getting replaced by the restore


## Verification Steps
1. Setup a 3 nodes harvester
1. Create a VM w/ extra disk and some data
1. Backup and shutdown VM
1. Start to observe `pod/virt-launcher-VMNAME` to get the node VM restoring on for next step. 
1. Initiate a restore with existing VM, get node info from `pod/virt-launcher-VMNAME`.
   ![image](https://github.com/harvester/tests/assets/2773781/eb3750eb-26a1-4785-b2d5-a41a4c749dcb)

1. While the restore is in progress and VM is starting on a node, shut down the node

## Expected Results
1. 1st restore should fail 
   ![image](https://github.com/harvester/tests/assets/2773781/49fcf50e-6c84-4198-bc91-b42cbc123c51)
   
2. VM should be restore to another node and `Running`
   ![image](https://github.com/harvester/tests/assets/2773781/a316c185-3a43-44be-a9d3-a65480837b18)
   
3. Test data still available and not broken
   ![image](https://github.com/harvester/tests/assets/2773781/62cd07d1-9ba5-4ff9-9120-41695beb966d)
