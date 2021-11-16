---
title: 20-Create RKE1 Kubernetes Cluster	
---
1. Click Cluster Management
2. Click Cloud Credentials
3. Click createa and select `Harvester`
4. Input credential name
5. Select existing cluster in the `Imprted Cluster` list
6. Click Create

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/4a2f6a52-dac7-4a27-84b3-14cbeb4156aa)

7. Expand RKE1 Configuration
8. Add Template in `Node template`
9. Select Harvester
10. Select created cloud credential created
11. Select `default` namespace
12. Select ubuntu image 
13. Select network: `vlan1`
14. Provide SSH User: `ubuntu`

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/19ca6b90-4688-4ff3-8ecd-60982edf1950)

15. Provide template name, click create
16. Open Cluster page, click Create
17. Toggle `RKE1`
18. Provide cluster name
19. Provide Name Prefix
20. Select node template we just created
21. Check `etcd`
22. Check `Control Panel`

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/5242d19b-078b-4337-acd6-257ffc470e8e)

23. Click create

## Expected Results
1. Provision RKE1 cluster successfully with `Running` status
2. Can acccess RKE1 cluster to check all resources and services

## Known issues
This issue block the RKE 1 provisioning task
- [#1519 Unable to create RKE1 cluster in rancher by node driver, shows "waiting for ssh to be available"](https://github.com/harvester/harvester/issues/1519) 
