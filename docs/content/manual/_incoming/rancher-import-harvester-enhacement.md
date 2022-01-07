---
title: Rancher import harvester enhancement
---

* Related issues: [#1330](https://github.com/harvester/harvester/issues/1330) Http proxy setting download image

## Category: 
* Rancher Integration

## Environment setup
1. Install the latest rancher from docker command
```
$ sudo docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:v2.6.3
``` 


## Verification Steps
1. Installed a 3 nodes harvester cluster 
1. Import harvester to rancher in virtualization management 
1. Enable node driver and create cloud credential
1. Provision a RKE2 cluster in rancher 
1. Confirm RKE2 cluster is fully operated, can explore it 
![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/b29e812c-1430-4447-9e34-a52a92895140)
1. Shutdown all 3 nodes server machine
![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/c351d09f-4745-4b87-b9a4-30f91cb4ab1f)
1. Wait for 10 minutes
1. Power on all harvester nodes server machines
1. Confirm harvester is fully operated
1. Confirm RKE2 vm is back to running
![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/a97b7464-747b-4fee-8368-651270705106)
1. Check the RKE2 cluster status in rancher  


## Expected Results
The RKE2 cluster in rancher should turn back to `Running` with no error after harvester server node machine is fully power off and power on. 
