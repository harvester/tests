---
title: #1330 Rancher import harvester enhancement
---

* Related issues: [#1330](https://github.com/harvester/harvester/issues/1330) Http proxy setting download image

## Environment setup
1. Install the latest rancher from docker command
```
$ sudo docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:v2.6-head
``` 
2. Create an one node harvester cluster 
3. Both harvester and rancher have internet connection


## Verification Steps
1. Access rancher dashboard
2. Open Virtualization Management page 
3. Import existing harvester 
4. Copy the registration url 
![image](https://user-images.githubusercontent.com/29251855/143001156-31b06586-9b66-4016-a0f5-6dca92a7b2f6.png)
5. Create image from URL (change folder date to latest)
https://cloud-images.ubuntu.com/focal/20211122/focal-server-cloudimg-amd64.img 
6. Access harvester dashboard
7. Edit `cluster-registration-url` in settings
![image](https://user-images.githubusercontent.com/29251855/143771558-01398c11-8e3f-40c1-903e-2817cade80c8.png)
8. Paste the registration url and save
9. Back to rancher and wait for harvester imported in Rancher


## Expected Results
1. Harvester can be imported in rancher dashboard with `running` status
2. Can access harvester in virtual machine page 
3. Can create harvester cloud credential
4. Can load harvester cloud credential while creating harvester
