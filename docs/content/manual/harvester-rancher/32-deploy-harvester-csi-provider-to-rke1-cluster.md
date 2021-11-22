---
title: 32-Deploy Harvester CSI provider to RKE 1 Cluster
---
1. Open `Cluster Management` page
1. Click Create 
1. Expand RKE1 Configuration
1. Add Template in `Node template`
1. Select Harvester
1. Select created cloud credential created
1. Select `default` namespace
1. Select ubuntu image 
1. Select network: `vlan1`
1. Provide SSH User: `ubuntu`
1. Provide template name, click create
1. Open Cluster page, click Create
1. Toggle `RKE1`
1. Provide cluster name
1. Provide Name Prefix
1. Select node template we just created
1. Check `etcd`
1. Check `Control Panel`
1. SSH to harvester cluster node 
1. Run the following command to generate add-on configuration 
```
./deploy/generate_addon.sh <serviceaccount name> <namespace>
```
1. Click the ```Edit as YAML``` button and add above command to it
1. Add the result to RKE YAML file 
1. Click create

## Expected Results
1. Provision RKE1 cluster successfully with `Running` status
1. Can acccess RKE1 cluster to check all resources and services
1. Check CSI provider installed and configured on RKE2 cluster

## Known issues
This issue block the RKE 1 provisioning task
- [#1519 Unable to create RKE1 cluster in rancher by node driver, shows "waiting for ssh to be available"](https://github.com/harvester/harvester/issues/1519) 