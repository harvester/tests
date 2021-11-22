---
title: 22-Create RKE2 Kubernetes Cluster	
---
1. Click Cluster Management
1. Click Cloud Credentials
1. Click createa and select `Harvester`
1. Input credential name
1. Select existing cluster in the `Imprted Cluster` list
1. Click Create

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/4a2f6a52-dac7-4a27-84b3-14cbeb4156aa)

1. Click Clusters 
1. Click Create
1. Toggle RKE2/K3s 
1. Select Harvester
1. Input `Cluster Name`
1. Select `default` namespace
1. Select ubuntu image 
1. Select network `vlan1`
1. Input SSH User: `ubuntu` 
1. Click Create

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/cbd9cc9b-60fb-4e81-985a-13fcaa88fa2f)

1. Wait for RKE2 cluster provisioning complete (~20min)

## Expected Results
1. Provision RKE2 cluster successfully with `Running` status

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/4526b95b-71f4-498f-b509-dea60ec5e0e5)

1. Can acccess RKE2 cluster to check all resources and services

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/682dccdc-cc0b-427f-ab7a-fdfaa1f82e06)
