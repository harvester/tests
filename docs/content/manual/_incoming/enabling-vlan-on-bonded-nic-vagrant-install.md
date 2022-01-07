---
title: Enabling vlan on a bonded NIC on vagrant install
---

* Related issues: [#1541](https://github.com/harvester/harvester/issues/1541) Enabling vlan on a bonded NIC breaks the Harvester setup

## Category: 
* Network

## Verification Steps
1. Pull ipxe example from https://github.com/harvester/ipxe-examples
2. Vagrant pxe install 3 nodes harvester
3. Access harvester settings page
4. Open `settings` -> `vlan`
5. Enable virtual network and set with `bond0`
6. Navigate to every page to check harvester is working
7. Create a vlan based on `bon0`

## Expected Results
Enable virtual network with `bond0` will not make harvester service out of work. 
![image](https://user-images.githubusercontent.com/29251855/143804059-f8fc0bee-b42a-4daa-b0bb-438b64b75db2.png)



