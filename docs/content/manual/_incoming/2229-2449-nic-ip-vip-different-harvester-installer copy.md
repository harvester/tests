---
title: NIC ip and vip can't be the same in Harvester installer
---

* Related issues: [#2229](https://github.com/harvester/harvester/issues/2229) [BUG] input nic ip and vip with same ip address in Harvester-Installer
* * Related issues: [#2449](https://github.com/harvester/harvester/issues/2449) [backport v1.0] [BUG] input nic ip and vip with same ip address in Harvester-Installer

## Category: 
* Harvester Installer

## Verification Steps
1. Launch ISO install process 
1. Set static node IP and gateway
![image](https://user-images.githubusercontent.com/29251855/173719118-1fd1609d-74f2-4f7d-9ff3-e1d21227e542.png)
1. Set the same node IP to the VIP field and press enter  
![image](https://user-images.githubusercontent.com/29251855/173719257-f60b55fd-0211-4fb7-8f45-3176eef4e577.png)

## Expected Results
* During Harvester ISO installer process, when we set static node IP address with the same one as the VIP IP address
* There will be an error message to prevent the installation process
`VIP must not be the same as Management NIC IP`
![image](https://user-images.githubusercontent.com/29251855/173719257-f60b55fd-0211-4fb7-8f45-3176eef4e577.png)
