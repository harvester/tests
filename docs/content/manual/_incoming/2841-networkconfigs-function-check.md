---
title: Networkconfigs function check
---

* Related issues: [#2841](https://github.com/harvester/harvester/issues/2841) [FEATURE] Reorganize the networkconfigs UI

  
## Category: 
* Network

## Verification Steps
1. Go to Cluster Networks/Configs
1. Create a cluster network and provide the name 
    ![image](https://user-images.githubusercontent.com/29251855/194039791-90a88cc0-879d-44d1-8b81-66a141c13732.png)
1. Create a Network Config 
1. Given the NICs that not been used by mgmt-bo (eg. `ens1f1`)  
    ![image](https://user-images.githubusercontent.com/29251855/194040174-72813f78-868f-4d02-9f79-023c61632994.png)
1. Use default `active-backup` mode 
1. Check the cluster network config in `Active` status
    ![image](https://user-images.githubusercontent.com/29251855/194040378-3f98d96a-b92a-4769-aff8-b3d16465ac80.png)
1. Go to Networks
1. Create a VLAN network
1. Given the name and vlan id
1. Select the cluster network from drop down list 
    ![image](https://user-images.githubusercontent.com/29251855/194040798-28aced46-38f1-47f6-b1e1-2c98f27fbe9e.png)
1. Check the vlan route activity 
    ![image](https://user-images.githubusercontent.com/29251855/194040915-e01d84a9-df2f-4188-8716-0caab5b04d04.png)
1. Check the NIC `ens1f1` can bind to the cnetwork-bo
    ```
    harvester-r2rpc:~ # ip a | grep cnetwork-bo
    3: ens1f1: <BROADCAST,MULTICAST,SLAVE,UP,LOWER_UP> mtu 1500 qdisc mq master cnetwork-bo state UP group default qlen 1000
    109: cnetwork-bo: <BROADCAST,MULTICAST,MASTER,UP,LOWER_UP> mtu 1500 qdisc noqueue master cnetwork-br state UP group default qlen 1000
    ```
1. Delete the created VLAN network 
1. Delete the network config from cluster network 
1. Delete the cluster network 
1. Create another cluster network `cnetwork2` without network config setup on it 
    ![image](https://user-images.githubusercontent.com/29251855/194046082-39eb8455-7012-46b8-bca5-c10b7d5d5374.png)

1. Go to create VLAN network page 
1. Provide vlan name and id 
1. Click the dropdown list and find the no config cluster network  


## Expected Results
1. Can create a new custom cluster network 
    ![image](https://user-images.githubusercontent.com/29251855/194043069-20737f1b-bad7-4d55-9528-7f40f3e9e828.png)

1. Can create network config based on available NICs ( for non `mgmt-bo`)
    ![image](https://user-images.githubusercontent.com/29251855/194043175-88305ba4-432c-41df-9d2b-cebdeb157713.png)

1. Can create VLAN network with valid id based on cluster network and config 
1. Can create custom VLAN network and route correctly in `active` status 
    ![image](https://user-images.githubusercontent.com/29251855/194043013-61d181d4-3c83-491a-8277-8368a4512ffc.png)

1. Can delete created custom VLAN network 
1. Can delete network config from cluster network 
    ![image](https://user-images.githubusercontent.com/29251855/194044275-d80645a3-116e-4685-bfa2-7a1a48f20948.png)
    ![image](https://user-images.githubusercontent.com/29251855/194044478-b983b904-66e6-48b4-ac50-7aaf6525ff4b.png)

1. Can delete created cluster network 
    ![image](https://user-images.githubusercontent.com/29251855/194044579-7b83218e-7071-4e44-9b04-50cc3ee324b1.png)
    ![image](https://user-images.githubusercontent.com/29251855/194044674-c752e029-d055-4526-8ecf-a357d1821416.png)
    ![image](https://user-images.githubusercontent.com/29251855/194044726-1d9c325a-d267-4b94-8412-3b343f045220.png)

1. Cluster network without any network config will display with `Not ready` on the VLAN creation drop down list  
    ![image](https://user-images.githubusercontent.com/29251855/194046416-814e496b-bc2e-4394-b2de-60acb2a9a1b5.png)
