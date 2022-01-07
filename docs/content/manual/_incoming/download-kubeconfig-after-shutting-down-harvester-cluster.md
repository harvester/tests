---
title: Download kubeconfig after shutting down harvester cluster
---

* Related issues: [#1475](https://github.com/harvester/harvester/issues/1475) After shutting down the cluster the kubeconfig becomes invalid

## Category: 
* Host

## Verification Steps
1. Shutdown harvester node 3, wait for fully power off
1. Shutdown harvester node 2, wait for fully power off
1. Shutdown harvester node 1, wait for fully power off
1. Wait for more than hours or over night
1. Power on node 1 to console page until you see management url 
![image](https://user-images.githubusercontent.com/29251855/145156486-60507643-8a96-4b4a-862d-367c41665e6b.png)

1. Power on node 2 to console page until you see management url 
1. Power on node 3 to console page until you see management url 
1. Confirm all nodes are in `Ready` status
1. Access harvester dashboard
1. Go to setting and click `Download Kubeconfig`
![image](https://user-images.githubusercontent.com/29251855/145156633-feddec8c-e322-404f-9104-7c543824f884.png)
1. ssh to each node and run `kubectl get pods -A` 

## Expected Results
1. Shutdown all 3 harvester cluster nodes machines and start after hours, can download the KubeConfig without error. 
1. Can run kubectl on all nodes correctly too. 
