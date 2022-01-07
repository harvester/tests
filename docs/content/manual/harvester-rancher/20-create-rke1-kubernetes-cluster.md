---
title: 20-Create RKE1 Kubernetes Cluster	
---
1. Click Cluster Management
1. Click Cloud Credentials
1. Click createa and select `Harvester`
1. Input credential name
1. Select existing cluster in the `Imported Cluster` list
1. Click Create

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/4a2f6a52-dac7-4a27-84b3-14cbeb4156aa)

1. Expand RKE1 Configuration
1. Add Template in `Node template`
1. Select Harvester
1. Select created cloud credential created
1. Select `default` namespace
1. Select ubuntu image 
1. Select network: `vlan1`
1. Provide SSH User: `ubuntu`

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/19ca6b90-4688-4ff3-8ecd-60982edf1950)

![image](https://user-images.githubusercontent.com/29251855/147911503-df997d2f-fa48-4ce9-876b-f309b1d6c7b1.png)

1. Provide template name, click create
![image](https://user-images.githubusercontent.com/29251855/147911570-7868367e-7729-4c4d-bfef-01751c76ed75.png)

1. Open Cluster page, click Create
1. Toggle `RKE1`
1. Provide cluster name
1. Provide Name Prefix
1. Select node template we just created
1. Check `etcd`
1. Check `Control Panel`

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/5242d19b-078b-4337-acd6-257ffc470e8e)

1. Select `harvester` as cloud provider
![image](https://user-images.githubusercontent.com/29251855/147911679-b99c0662-bf27-44a5-8702-1e9c526ae604.png)
1. Click create

## Expected Results
1. Provision RKE1 cluster successfully with `Running` status
1. Can acccess RKE1 cluster to check all resources and services
