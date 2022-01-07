---
title: Provision RKE2 cluster with resource quota configured
---

* Related issues: [#1455](https://github.com/harvester/harvester/issues/1455) Node driver provisioning fails when resource quota configured in project

* Related issues: [#1449](https://github.com/harvester/harvester/issues/1449) Incorrect naming of project resource configuration


## Category: 
* Rancher Integration

## Environment setup
1. Install the latest rancher from docker command
```
$ sudo docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:v2.6.3
``` 

## Test Scenarios
* Scenario 1:

  - Project with resource quota: 
     - CPU Limit / CPU Reservation: 6000 / 6144
     - Memory Limit / Memory Reservation: 6000 / 6144

* Scenario 2: 
  - Project resource quota: 
    - CPU Limit / CPU Reservation: 6 core / 6GB
    - Memory Limit / Memory Reservation: 6 core / 6GB

  - Container resource limit:
    - CPU limit/reservation: 2000/1000
    - Memory limit/reservation: 500/256

## Verification Steps
1. Import harvester from rancher 
1. Open Cluster management -> Driver
1. Create cloud credential
1. Access harvester from virtualization management page
1. Create a new project `test-1561-proj` and assign the following resource quota value

 * Project resource quota: 
   - CPU Limit / CPU Reservation: 6000 / 6144
   - Memory Limit / Memory Reservation: 6000 / 6144
 
 * Namespace resource quota: None (default) 

1. Create a namespace `test-1561-ns` under the `test-1561-proj`
1. Provision a rke2 cluster with 2 CPU and 4GB memory and set namespace to `test-1561-ns`
1. Create a new project `test-project2` and and assign the following resource quota value
    
* Project resource quota: 
  - CPU Limit / CPU Reservation: 6 core / 6GB
  - Memory Limit / Memory Reservation: 6 core / 6GB
 
 * Namespace resource quota: None (default)
 * Container resource limit:
   - CPU limit/reservation: 2000/1000
   - Memory limit/reservation: 500/256

![image](https://user-images.githubusercontent.com/29251855/143868981-ba38d935-63df-468a-a6d8-58189abc4671.png)

1.  Provision a rke2 cluster with `1` CPU and `1GB` memory and set namespace to `test-namespace2`
![image](https://user-images.githubusercontent.com/29251855/143870073-2eb56d39-ae21-4b50-ba3f-b035d258bb2d.png)

## Expected Results
1. The `1st scenario` can provision RKE2 cluster with VM successfully created and running with resource quota configured on project and default setting on namespace.


2. The `2nd scenario` can provision RKE2 cluster with VM successfully created and running with resource quota configured on project, default setting on namespace, and container resource quota configured


