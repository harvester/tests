---
title: Prevent normal users create harvester-public namespace
---

* Related issues: [#2485](https://github.com/harvester/harvester/issues/2485) [FEATURE] [Harvester Node Driver v2] Prevent normal users from creating VMs in harvester-public namespace

  
## Category: 
* Rancher integration

## Verification Steps
1. Import Harvester from Rancher
1. Create standard `user` in Rancher User & Authentication
1. Edit Harvester in virtualization Management, assign Cluster Member role to user 
    ![image](https://user-images.githubusercontent.com/29251855/191748214-50fd7290-e2ae-4910-9a27-c9b67c581886.png)
1. Login with user 
1. Create cloud credential 
1. Provision an RKE2 cluster 
1. Check the namespace dropdown list

## Expected Results
1. Now the standard user with cluster member rights won't display `harvester-public` while user node driver to provision the RKE2 cluster.  

    ![image](https://user-images.githubusercontent.com/29251855/191777382-739a814a-d1e8-4627-b80f-2e20eecc2991.png)

1. Cluster member `user` can see harvester-public in Harvester
    ![image](https://user-images.githubusercontent.com/29251855/191778155-2e837ae2-aeb7-4697-908c-04b4b7041cfe.png)