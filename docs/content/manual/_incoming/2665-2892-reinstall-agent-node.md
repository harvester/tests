---
title: Reinstall agent node
---

* Related issues: [#2665](https://github.com/harvester/harvester/issues/2665) [BUG] reinstall 1st node

* Related issues: [#2892](https://github.com/harvester/harvester/issues/2892) [BUG] rancher-system-agent keeps showing error on a new node in an upgraded cluster
   
## Category:
* Host

## Verification Steps
### Test Plan 1: Reinstall management node and agent node in a upgraded cluster
1. Create a 4-node v1.0.3 cluster.
1. Upgrade the master branch:
1. Check the spec content in `provisioning.cattle.io/v1/clusters -> fleet-local`
   ![image](https://user-images.githubusercontent.com/29251855/196139161-7b6e6e84-692d-4f4f-a978-62fc50f64f06.png)
1. Check the iface content in `helm.cattle.io/v1/helmchartconfigs -> rke2-canal`
   ![image](https://user-images.githubusercontent.com/29251855/196141139-e4ff668e-287a-4722-865d-a7c0f145c862.png)
   ```
      spec:                                                                                                                                                                                      │
   │   valuesContent: |-                                                                                                                                                                        │
   │     flannel:                                                                                                                                                                               │
   │       iface: "" 
   ```

1. Remove the agent node and 1 management node. Remove agent node (node 4)
   ![image](https://user-images.githubusercontent.com/29251855/196138324-83b64d50-0236-4110-86c2-551ae046a406.png)
   ![image](https://user-images.githubusercontent.com/29251855/196138906-e77de8f0-d61d-4a91-82b2-e36cbbb6462a.png)
  
1. Remove management node (node 3)
   ![image](https://user-images.githubusercontent.com/29251855/196139707-ce8cc444-21fb-4bba-a040-9b09e0ae7fa9.png)
   ![image](https://user-images.githubusercontent.com/29251855/196139906-ff92320f-f5f7-4fb5-af20-5cf0f3fe36b9.png)
   ![image](https://user-images.githubusercontent.com/29251855/196147230-7c0b1835-c219-41b2-b0b8-32bae9962f27.png)

1. After the node is removed, provision a new node.
1. Check the node can join the cluster and can be promoted as a management node.
1. After we have 3 management nodes, provision a new node and check if it can join the cluster.  

### Test Plan 2: Reinstall management node and agent node in a new Harvester cluster
1. Create a 4-node v1.0.3 cluster.
1. Upgrade to the v1.1.0-rc3
1. Remove the agent node and the first management node 
1. Remove agent node (node 4)
      ![image](https://user-images.githubusercontent.com/29251855/196345973-36d62a3d-e2a5-4261-90a6-4d7e89425726.png)
      ![image](https://user-images.githubusercontent.com/29251855/196346046-76f1ceb3-a5a2-4988-bb3f-3dc090383199.png)
      ![image](https://user-images.githubusercontent.com/29251855/196346128-5e69b595-241a-4c15-b6ac-2f967e4561f4.png)

1. Remove management node (node 1)
      ![image](https://user-images.githubusercontent.com/29251855/196347345-1ff6de57-8870-4592-ba36-1039be6a9e09.png)
      ![image](https://user-images.githubusercontent.com/29251855/196347501-417a40a5-a669-4d21-b94e-d9f546737085.png)

1. After the node is removed, provision a new node.
1. Check the node can join the cluster and can be promoted as a management node. (node 1) 
1. After we have 3 management nodes, provision a new node and check if it can join the cluster. (node 4)

## Expected Results

### Test Result 1
1. Can successfully re-join the management node after upgrade 
  ![image](https://user-images.githubusercontent.com/29251855/196159969-9c8acb11-b9fe-4501-94d5-74545579ef4d.png)

1. Can successfully re-join the agent node after upgrade 
  ![image](https://user-images.githubusercontent.com/29251855/196164183-20c4498a-c4c6-4033-a527-d3c8ff84f8aa.png)


### Test Result 2
Verified after upgrading from v1.0.3 to `v1.1.0-rc3`,we **can rejoin** the management node and agent node back correctly. 

1. Successfully re-join the management node after upgrade 
   ![image](https://user-images.githubusercontent.com/29251855/196353489-ea323d20-4028-411a-ba32-5fbb7ae4ae2f.png)
   ![image](https://user-images.githubusercontent.com/29251855/196353521-6882c3e4-f374-4c9f-a190-8b5929b8e9e5.png)

1. Successfully re-join the agent node after upgrade 
   ![image](https://user-images.githubusercontent.com/29251855/196358018-f9b7f72c-cfa4-4e6f-a25e-a8818e1f491b.png)
   ![image](https://user-images.githubusercontent.com/29251855/196358073-29b879be-1e0c-465e-9327-6430111d4436.png)