---
title: Dashboard Storage usage display when node disk have warning
---

* Related issues: [#2622](https://github.com/harvester/harvester/issues/2622) [BUG] Dashboard Storage used is wrong when a node disk is warning

  
## Category: 
* Storage

## Verification Steps
1. Login harvester dashboard
1. Access Longhorn UI from url https://192.168.122.136/dashboard/c/local/longhorn 
1. Go to Node page 
1. Click edit node and disks
1. Select disabling Node scheduling
    ![image](https://user-images.githubusercontent.com/29251855/187578343-653d0235-92a9-4979-aae0-b62b606df525.png)
1. Select disabling storage scheduling on the bottom
    ![image](https://user-images.githubusercontent.com/29251855/187578175-326b5909-cd6a-4e31-a1cf-92df5e619a5c.png)
1. Open Longhorn dashboard page, check the Storage Schedulable 
1. Open Harvester dashboard page, check the used and scheduled storage size  

## Expected Results
After disabling the node and storage scheduling on Longhorn UI. 
1. The scheduled storage display 0 Bi on Longhorn dashboard 
    ![image](https://user-images.githubusercontent.com/29251855/187577965-99dc5c6f-c270-4546-8c48-d93bb462e5a7.png)
 
1. And Harvester dashboard also display 0 used and scheduled in correspondence with Longhorn UI
    ![image](https://user-images.githubusercontent.com/29251855/187606026-a735994b-6527-417f-b0e3-e8da183afe73.png)