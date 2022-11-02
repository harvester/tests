---
title: Check volume status after upgrade
---

* Related issues: [#2920](https://github.com/harvester/harvester/issues/2920) [BUG] Volume can't turn into healthy when upgrading from v1.0.3 to v1.1.0-rc2 
  
## Category: 
* Volume

## Verification Steps
1. Prepare a 4 nodes v1.0.3 Harvester cluster 
1. Install several images
1. Create three VMs
1. Enable Network 
1. Create vlan1 network
1. Shutdown all VMs
1. Upgrade to v1.1.0-rc3
1. Check the volume status in Longhorn UI
1. Open K9s, Check the pvc status after upgrade 

## Expected Results
1. Can finish the pre-drain of each node and successfully upgrade to v1.1.0-rc3
    ![image](https://user-images.githubusercontent.com/29251855/196434398-a61b5111-7723-4fa6-ac57-2a68ffef73ee.png)

1. Volume status after upgrade in Longhorn UI did not have `degraded` status
    ![image](https://user-images.githubusercontent.com/29251855/196433439-90b9fee5-0c20-4216-b91d-a866a27f9c62.png)

1. The pvc volume status after upgrade
    ![image](https://user-images.githubusercontent.com/29251855/196433662-b3add848-9f82-4277-83a8-e13df352b09d.png)