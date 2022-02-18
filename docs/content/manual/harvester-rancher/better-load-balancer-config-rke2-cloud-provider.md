---
title: Better Load Balancer Config of Harvester cloud provider
---

 * Related issue: [#1435](https://github.com/harvester/harvester/issues/1435) better loadblancer config of Harvester cloud provider

## Category: 
* Rancher Integration

## Environment setup
1. Install rancher `2.6.3` by docker
```
docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:v2.6.3
```

## Verification Steps
1. Import harvester to rancher virtualization management
1. Create a harvester cluster by harvester driver
1. Access the new harvester cluster from rancher cluster management
1. Create a load balancer from service discovery -> services
1. Re login rancher
1. Open create load-balance page
1. Click ctrl+R to refresh page
1. Check the "Add-on Config" tabs

## Expected Results
1. User can configure `port`, `IPAM` and `health check` related setting on `Add-on Config` page
![image](https://user-images.githubusercontent.com/29251855/141245366-799057f1-2aa7-4d7a-90d2-5e11541ddbc3.png)

1. Can create load balancer correctly with health check setting