---
title: 29-Deploy Harvester cloud provider to RKE2 Cluster	
---
1. Click Clusters 
1. Click Create
1. Toggle RKE2/K3s
1.  Select Harvester
1.  Input `Cluster Name`
1.  Select `default` namespace
1.  Select ubuntu image 
1.  Select network `vlan1`
1.  Input SSH User: `ubuntu`
1. Check alread set `Harvester` as cloud provider

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/514d1d88-08e7-441a-861c-38bb3c96bbe7)

1. Click Create
1. Wait for RKE2 cluster provisioning complete (~20min)

## Expected Results
1. Provision RKE2 cluster successfully with `Running` status

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/4526b95b-71f4-498f-b509-dea60ec5e0e5)

1. Can acccess RKE2 cluster to check all resources and services

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/682dccdc-cc0b-427f-ab7a-fdfaa1f82e06)
