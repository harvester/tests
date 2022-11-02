---
title: VM label names consistentency before and after the restore
---

* Related issues: [#2662](https://github.com/harvester/harvester/issues/2662) [BUG] VM label names should be consistent before and after the restore task is done

  
## Category: 
* Network

## Verification Steps
1. Create a VM named `ubuntu`
1. Check the label name in virtual machine yaml content, label marked with `harvesterhci.io/vmName`
    ![image](https://user-images.githubusercontent.com/29251855/188374691-b36db1bc-2e2e-447b-96e1-699aa5e0ffee.png)
1. Setup the S3 backup target 
1. Take a S3 backup with name 
1. After the backup task is done, delete the current VM
1. Restore VM from the backup with the same name `ubuntu` (Create New)
    ![image](https://user-images.githubusercontent.com/29251855/188378123-9af171af-c992-4e78-bdbb-8627903502ff.png)
1. Check the yaml content after VM fully operated 

## Expected Results
The vm lable name is consistent to display `harvesterhci.io/vmName` after restore from the backup.

1. When created a new VM, the vm label name marked with `harvesterhci.io/vmName`
    ![image](https://user-images.githubusercontent.com/29251855/188374691-b36db1bc-2e2e-447b-96e1-699aa5e0ffee.png)

1. After new VM restored from backup with the same name, the vm label name still marked with `harvesterhci.io/vmName`
    ![image](https://user-images.githubusercontent.com/29251855/188379642-a699f0ba-5731-41ae-be18-de5603744b8c.png)