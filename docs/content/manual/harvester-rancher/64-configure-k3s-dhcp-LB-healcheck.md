---
title: 62-Configure the K3s "DHCP" LoadBalancer service
---
Prerequisite: 
Already provision K3s cluster and cloud provider on test plan 
* 59-Create K3s Kubernetes Cluster 
* 61-Deploy Harvester cloud provider to k3s Cluster
* 62-Configure the K3s "DHCP" LoadBalancer service

1. A `Working` DHCP load balancer service created on K3s cluster
1. Edit Load balancer config
1. Check the "Add-on Config" tabs
1. Configure `port`, `IPAM` and `health check` related setting on `Add-on Config` page
![image](https://user-images.githubusercontent.com/29251855/141245366-799057f1-2aa7-4d7a-90d2-5e11541ddbc3.png)


## Expected Results
1. Can create load balance service correctly
1. Can route workload to nginx deployment