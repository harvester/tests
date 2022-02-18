---
title: Use template to create cluster through virtualization management
---

 * Related issue: [#1620](https://github.com/harvester/harvester/issues/1620) User is unable to use template to create cluster through virtualization management

## Category: 
* Rancher Integration

## Environment setup
1. Install rancher `2.6.3` by docker
```
docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:v2.6.3
```

## Verification Steps
1. Import harvester from rancher through harvester settings
1. Access harvester from rancher virtualization management page
1. Open Virtual Machine page 
1. Click create 
1. Check `Use VM Template`
1. Select one of the template
1. Create VM according to the template 

## Expected Results
Access harvester from Rancher, on virtual machine page can load default three template to create VM. 

**iso image base template**

![image](https://user-images.githubusercontent.com/29251855/145583546-59cea4ea-4072-437e-9cf7-2449776abb56.png)

**raw image base template**
![image](https://user-images.githubusercontent.com/29251855/145583593-5aa7c897-f3dc-4fa1-9b94-750794a3e88e.png)

**windows iso image base tempalte**
![image](https://user-images.githubusercontent.com/29251855/145583672-72255932-72ee-4a88-b38a-8830789040c8.png)

**Create vm with iso template**
![image](https://user-images.githubusercontent.com/29251855/145586368-5a5b640b-3955-403b-8149-ff8657e2aa26.png)
