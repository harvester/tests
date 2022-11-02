---
title: Deny the vlanconfigs overlap with the other
---

* Related issues: [#2828](https://github.com/harvester/harvester/issues/2828) [BUG][FEATURE] Deny the vlanconfigs overlap with the other

  
## Category: 
* Network

## Verification Steps
1. Prepare a 3 nodes Harvester on local kvm
1. Each VM have five NICs attached.
1. Create a cluster network `cn1`
1. Create a vlanconfig `config-all` which applied to `all nodes`
  ![image](https://user-images.githubusercontent.com/29251855/196409238-dd1a5d9f-bf00-46cd-93b2-c9469bf7c58a.png)
1. Set one of the NIC
  ![image](https://user-images.githubusercontent.com/29251855/196409451-5279f4e5-e66a-4960-8889-cc1c186acfdc.png)
1. On the same cluster network, create another vlan network `config-one` which applied to only `node 1`
  ![image](https://user-images.githubusercontent.com/29251855/196409565-67e2e418-1efc-4c50-a016-7fea4dd582a3.png)
1. Provide another NIC
  ![image](https://user-images.githubusercontent.com/29251855/196409613-e214183d-b665-453e-8fa8-246f21a11243.png)
1. Click the create button


## Expected Results
Under the same Cluster Network:
1. When we create vlanconfig on the node that already been applied earlier by another vlanconfig, 
it will promopt the following error to prevent creation
`admission webhook "validator.harvester-system.harvester-network-webhook" denied the request: Internal error occurred: could not create vlanConfig config-one because it overlaps with other vlanconfigs matching node(s) [n1-110rc3]`
    ![image](https://user-images.githubusercontent.com/29251855/196409690-54943dac-717e-4bb0-9496-ec85706f2326.png)