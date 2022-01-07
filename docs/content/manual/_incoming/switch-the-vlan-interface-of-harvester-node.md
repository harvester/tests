---
title: Switch the vlan interface of harvester node
---

* Related issues: [#1464](https://github.com/harvester/harvester/issues/1464) VM pods turn to the terminating state after switching the VLAN interface

## Category: 
* Network

## Verification Steps
1. User ipxe-example to build up 3 nodes harvester 
1. Login harvester dashboard -> Access Settings 
1. Enable vlan network with `harvester-mgmt` NIC interface
1. Create a VM using `harvester-mgmt`
1. Disable vlan network
1. Enable vlan network and select `bond0` interface
![image](https://user-images.githubusercontent.com/29251855/144204800-ed20ab79-0c18-4a70-b258-2468d62e072d.png)
1. Check host and vm is working 
1. Directly switch network interface from `bond0` to `harvester-mgmt` without disable it.
![image](https://user-images.githubusercontent.com/29251855/144206080-cbba3e29-b125-422a-b629-9a412a218feb.png)
1. Check host and vm is working 

## Expected Results
1. Switch the VLAN interface of this host can't affect Host and VM operation. 
1. All harvester node keep in `running` status 

![image](https://user-images.githubusercontent.com/29251855/144206164-092272aa-0488-40f4-bb3d-4a1aea5fdb5d.png)

![image](https://user-images.githubusercontent.com/29251855/144207427-79056433-94d6-4d2f-9680-5a55a9d80efe.png)

