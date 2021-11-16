---
title: 32-Deploy Harvester CSI provider to RKE 1 Cluster
---
1. Open `Cluster Management` page
2. Click Create 
3. Expand RKE1 Configuration
4. Add Template in `Node template`
5. Select Harvester
6. Select created cloud credential created
7. Select `default` namespace
8. Select ubuntu image 
9. Select network: `vlan1`
10. Provide SSH User: `ubuntu`
11. Provide template name, click create
12. Open Cluster page, click Create
13. Toggle `RKE1`
14. Provide cluster name
15. Provide Name Prefix
16. Select node template we just created
17. Check `etcd`
18. Check `Control Panel`
19. SSH to harvester cluster node 
20. Run the following command to generate add-on configuration 
```
./deploy/generate_addon.sh <serviceaccount name> <namespace>
```
22. Click the ```Edit as YAML``` button and add above command to it
23. Add the result to RKE YAML file 
24. Click create

## Expected Results
1. Provision RKE1 cluster successfully with `Running` status
2. Can acccess RKE1 cluster to check all resources and services
3. Check CSI provider installed and configured on RKE2 cluster

## Known issues
This issue block the RKE 1 provisioning task
- [#1519 Unable to create RKE1 cluster in rancher by node driver, shows "waiting for ssh to be available"](https://github.com/harvester/harvester/issues/1519) 