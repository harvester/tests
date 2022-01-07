---
title: VIP configured in a VLAN network should be reached 
---

 * Related issue: [#1424](https://github.com/harvester/harvester/issues/1424) VIP configured in a VLAN network can not be reached 

## Category: 
* Network

## Environment Setup
* The network environment must have vlan network configured and also have DHCP server prepared on your testing vlan

## Verification Steps
1. Enable virtual network with `harvester-mgmt`
1. Open Network -> Create a virtual network
1. Provide network name and correct vlan id 
![image](https://user-images.githubusercontent.com/29251855/148182659-5b0f0d14-2654-4123-a417-4bd4e101b597.png)
1. Open Route, use the default `auto` setting
![image](https://user-images.githubusercontent.com/29251855/148182727-a445667c-fc78-4c83-a3d5-0238b8d2b17c.png)
1. Create a VM and use the created route 
1. SSH to harvester node
1. Ping the IP of the created VM
1. Create a virutal network
1. Provide network name and correct vlan id 
1. Open Route, use the `manual` setting
1. Provide the `CIDR` and `Gateway` value
![image](https://user-images.githubusercontent.com/29251855/148185885-b2c5b075-bd08-4fd6-97ad-7485a67e9339.png)
1. Repeat step 5 - 7

## Expected Results
1. Check the `auto` route vlan can be detected with `running` status
![image](https://user-images.githubusercontent.com/29251855/148183159-1242ad24-ee44-4428-8592-abdfa5d863fc.png)
1. Check the `manual` route vlan can be detected with `running` status
1. Check the VM can get IP based on `auto` or `manual` vlan route
1. Check can ping VM IP from harvester node 
