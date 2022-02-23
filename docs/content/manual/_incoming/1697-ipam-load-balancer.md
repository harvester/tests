---
title: Check IPAM configuration with IPAM
---
* Related issues: [#1697](https://github.com/harvester/harvester/issues/1697) Optimization for the Harvester load balancer

## Verification Steps

1. Install the latest rancher and import a Harvester cluster
1. Create a cluster by Harvester node driver
1. Navigate to the workload Page, create a workload
1. Click "Add ports", select type as LB, protocol as TCP
1. Check IPAM selector
1. Navigate to the service page, create a LB
1. Click "Add-on config" tab and check IPAM and port
![image.png](https://user-images.githubusercontent.com/83787952/152212105-2b2335be-b12b-42ac-bfcf-aa1d2aeb6fd3.png)
![image.png](https://user-images.githubusercontent.com/83787952/152212109-039a3e23-9eae-4ffc-9318-58f048a112c1.png)