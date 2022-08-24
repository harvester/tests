---
title: Local cluster user input topology key
---

* Related issues: [#2567](https://github.com/harvester/harvester/issues/2567) [BUG] Local cluster owner create Harvester cluster failed(RKE2)

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
1. Check can input Topology key value 
## Expected Results
1. Login with cluster owner role and provision a RKE2 cluster
1. we can input the topology key in the Topology key field of the pod selector 
![image](https://user-images.githubusercontent.com/29251855/182752496-1fa49c1d-1b93-4147-9d5b-ef3a56d5bd2b.png)