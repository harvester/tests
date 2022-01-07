---
title: Check can apply the resource quota limit to project and namespace 
---

* Related issues: [#1454](https://github.com/harvester/harvester/issues/1454) Incorrect memory unit conversion in namespace resource quota

## Category: 
* Rancher Integration

## Environment setup
1. Install the latest rancher from docker command
```
$ sudo docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:v2.6.3
``` 

## Verification Steps
1. Access Rancher dashboard
1. Open Cluster management -> Explore the active cluster
1. Create a new project `test-1454-proj` in Projects/Namespaces
1. Set resource quota for the project 
  * Memory Limit:
    - Project Limit: 512
    - Namespace default limit: 256
  * Memory Reservation:
    - Project Limit: 256
    - Namespace default limit: 128
1. Click create namespace `test-1454-ns` under project `test-1454-proj`
1. Click `Kubectl Shell` and run the following command
  * kubectl get ns
  * kubectl get quota -n test-1454-ns
1. Check the output 
1. Click `Workload` -> `Deployments` -> `Create`
1. Given the `Name`, `Namespace` and `Container image`
![image](https://user-images.githubusercontent.com/29251855/143847775-eb84fa49-54d5-4001-a210-cbd8ed1235d1.png)
1.  Click Create

## Expected Results
Based on configured project resource limit and namespace default limit, 

1. The memory limit of 256 Megabytes and memory reservation of 128 Megabytes can be configured and applied to project correctly.

![image](https://user-images.githubusercontent.com/29251855/143846876-41021ccf-86a3-40b5-81ca-101800444bee.png)

![image](https://user-images.githubusercontent.com/29251855/143847197-d340a01d-5c4f-4d15-a7c9-2b470a9f72ff.png)

![image](https://user-images.githubusercontent.com/29251855/143846795-915a4445-2e0d-4349-a8c4-100fbaf13efb.png)

