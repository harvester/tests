---
title: Rejoin node machine after Harvester upgrade
---

* Related issues: [#2655](https://github.com/harvester/harvester/issues/2655) [BUG] reinstall 1st node


## Category: 
* Upgrade Harvester


## Environment requirement
1. Network environment has available VLAN id setup on DHCP server
1. DHCP server has setup the IP range can allocate to above VLAN id
1. Harvester node can route to DHCP server through VLAN id to retrieve IP address
1. Network has at least two NICs
1. Suggest not to use SMR type HDD disk


## Verification Steps
1. Create a 3 nodes v1.0.3 Harvester cluster.
1. Upgrade the master branch:
1. Remove the agent node and 1 management node.
      - Remove agent node (node 4)
     ![image](https://user-images.githubusercontent.com/29251855/196138324-83b64d50-0236-4110-86c2-551ae046a406.png)
     ![image](https://user-images.githubusercontent.com/29251855/196138906-e77de8f0-d61d-4a91-82b2-e36cbbb6462a.png)
     
     - Remove management node (node 3)
     ![image](https://user-images.githubusercontent.com/29251855/196139707-ce8cc444-21fb-4bba-a040-9b09e0ae7fa9.png)
     ![image](https://user-images.githubusercontent.com/29251855/196139906-ff92320f-f5f7-4fb5-af20-5cf0f3fe36b9.png)
     ![image](https://user-images.githubusercontent.com/29251855/196147230-7c0b1835-c219-41b2-b0b8-32bae9962f27.png)

1. After the node is removed, provision a new node.
1. Check the node can join the cluster and can be promoted as a management node.
1. After we have 3 management nodes, provision a new node and check if it can join the cluster.

## Expected Results
1. Verify after Harvester upgrade complete, we **can rejoin** the management node and agent node back correctly. 

1. Can re-join the management node after upgrade 
  ![image](https://user-images.githubusercontent.com/29251855/196159969-9c8acb11-b9fe-4501-94d5-74545579ef4d.png)

1. Can re-join the agent node after upgrade 
  ![image](https://user-images.githubusercontent.com/29251855/196164183-20c4498a-c4c6-4033-a527-d3c8ff84f8aa.png)
1. Can create new vms on the newly joined node.
1. Can restore vms/migrate on the newly joined node.

