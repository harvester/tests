---
title: Topology aware scheduling of guest cluster workloads
---

* Related issues: [#1418](https://github.com/harvester/harvester/issues/1418) [FEATURE] Support topology aware scheduling of guest cluster workloads
* Related issues: [#2383](https://github.com/harvester/harvester/issues/2383) [backport v1.0.3] [FEATURE] Support topology aware scheduling of guest cluster workloads

## Category: 
* Rancher integration

## Verification Steps
1. Environment preparation as above steps
1. Access Harvester node config page 
1. Add the following node labels with values
 - topology.kubernetes.io/zone
 - topology.kubernetes.io/region
1. Provision an RKE2 cluster 
1. Wait for the provisioning complete
1. Access RKE2 guest cluster 
1. Open Workload deployments
1. Edit the yaml of cloud provider 
![image](https://user-images.githubusercontent.com/29251855/177773323-2152dd4e-9b8e-431a-ab5b-a72f1bc94f6a.png)
1. Replace the image version to `rancher/harvester-cloud-provider:v0.1.4`
![image](https://user-images.githubusercontent.com/29251855/177774896-4c2cef6c-148b-4366-a822-c859416b3f34.png)
1. Delete the original v0.1.13 cloud provider deployment to let the latest one can be created correctly
1. Access the RKE2 cluster in Cluster Management page 
1. Click + to add another node 
![image](https://user-images.githubusercontent.com/29251855/177774100-63c1a229-19d4-45f7-bd4e-8d2453c9149f.png) 
1. Access the RKE2 cluster node page
![image](https://user-images.githubusercontent.com/29251855/177774234-ed001086-75a2-46e7-9638-0771cc790fad.png)
1. Wait until the second node created
![image](https://user-images.githubusercontent.com/29251855/177774368-0c8b6ac1-15f0-4a64-8945-85551dc85e4f.png)
1. Edit yaml of the second node 
1. Check the harvester node label have propagated  to the guest cluster node 
![image](https://user-images.githubusercontent.com/29251855/177774559-8f278b2d-fff0-48ec-a62f-ceb3a9da8cc3.png)

## Expected Results
* The topology encoded in the Harvester cluster node labels
![image](https://user-images.githubusercontent.com/29251855/177771658-1e3a8336-61c7-459d-9d4f-19e626ce9f23.png)

* Can be correctly propagated to the additional node of the RKE2 guest cluster
![image](https://user-images.githubusercontent.com/29251855/177757013-d04214d3-3f70-4331-b4ab-663e19e2a816.png)
![image](https://user-images.githubusercontent.com/29251855/177757261-da51ac4e-806b-48a0-ac32-f2b4c10d3e0b.png)