---
title: Polish harvester machine config in Rancher
---

* Related issues: [#2598](https://github.com/harvester/harvester/issues/2598) [BUG]Polish harvester machine config

  
## Category: 
* Rancher integration

## Verification Steps
1. Import Harvester from Rancher 
1. Create a standard user `local` in Rancher User & Authentication
1. Open Cluster Management page 
1. Edit cluster config 
    ![image](https://user-images.githubusercontent.com/29251855/182781682-5cdd3c6a-517b-4f61-980d-3ee3cab86745.png)
1. Expand Member Roles
1. Add `local` user with Cluster Owner role
    ![image](https://user-images.githubusercontent.com/29251855/182781823-b71ba504-6488-4581-b50d-17c333496b8c.png)
1. Create cloud credential of Harvester
1. Login with `local` user
1. Open the provisioning RKE2 cluster page 
1. Select Advanced settings
1. Add Pod Scheduling
1. Select `Pods in these namespaces`
1. Check the list of available pods with the namespaces options above
1. Check can input Topology key value 
1. Access Harvester UI (Not from Rancher)
1. Open project/namespace
1. Create several namespaces 
1. Login `local` user to Rancher 
1. Open the the provisioning RKE2 cluster page 
1. Check the available `Pods in these namespaces` list have been updated

## Expected Results
Checked the following test plan for `RKE2` cluster are working as expected

1. Available namespace options are affiliated with (the same as) what we show in the management cluster namespace list
    ![image](https://user-images.githubusercontent.com/29251855/182752411-b970a295-96d8-4576-a4db-d397953c7249.png)
    ![image](https://user-images.githubusercontent.com/29251855/182752437-733a7843-2f06-4a38-a810-5b9a42916f24.png)
1. We can input the topology key in the Topology key field of the pod selector
    ![image](https://user-images.githubusercontent.com/29251855/182752496-1fa49c1d-1b93-4147-9d5b-ef3a56d5bd2b.png)

1. We can get the updated namespace list of cluster in the pod selector
    ![image](https://user-images.githubusercontent.com/29251855/182754019-b2aab60f-1060-49e2-8442-543195b805bc.png)