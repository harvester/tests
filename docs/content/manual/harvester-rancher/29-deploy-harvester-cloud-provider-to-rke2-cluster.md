---
title: 29-Deploy Harvester cloud provider to RKE2 Cluster	
---
1. Click Clusters 
2. Click Create
3. Toggle RKE2/K3s
4.  Select Harvester
5.  Input `Cluster Name`
6.  Select `default` namespace
7.  Select ubuntu image 
8.  Select network `vlan1`
9.  Input SSH User: `ubuntu`
10. Check alread set `Harvester` as cloud provider

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/514d1d88-08e7-441a-861c-38bb3c96bbe7)

11. Click Create
12. Wait for RKE2 cluster provisioning complete (~20min)

## Expected Results
1. Provision RKE2 cluster successfully with `Running` status

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/4526b95b-71f4-498f-b509-dea60ec5e0e5)

2. Can acccess RKE2 cluster to check all resources and services

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/682dccdc-cc0b-427f-ab7a-fdfaa1f82e06)
