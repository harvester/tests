---
title: The count of volume snapshots should not include VM's snapshots
---

* Related issues: [#3004](https://github.com/harvester/harvester/issues/3004) [BUG] The count of volume snapshots should not include VM's snapshots
  
## Category: 
* Volume

## Verification Steps
1. Create a VM `vm1`
1. Take a VM snapshot
1. Check the volume snapshot page
1. Check the VM snapshot page

## Expected Results
1. When one VM is created 
    ![image](https://user-images.githubusercontent.com/29251855/197482909-baf7d1f4-4032-4180-bb88-22aac8b9a8bc.png)

1. Only VM snap are created
    ![image](https://user-images.githubusercontent.com/29251855/197484294-46b89b29-78be-4d28-a33c-77aa525850a8.png)

1. The count of volume snapshots should not include VM's snapshots.
    ![image](https://user-images.githubusercontent.com/29251855/197484528-ed4c562b-782b-400e-99ec-fa97e292568d.png)
