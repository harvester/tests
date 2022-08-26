---
title: VM IP addresses should be labeled per network interface
---

* Related issues: [#2032](https://github.com/harvester/harvester/issues/2032) [BUG] VM IP addresses should be labeled per network interface
* Related issues: [#2370](https://github.com/harvester/harvester/issues/2370) [backport v1.0.3] VM IP addresses should be labeled per network interface

## Category: 
* Virtual Machine

## Verification Steps
1. Enable network with magement-mgmt interface
1. Create vlan network `vlan1` with id `1`
1. Check the IP address on the VM page
1. Create a VM with `harvester-mgmt` network
1. Import Harvester in Rancher 
1. Provision a RKE2 cluster from Rancher 
1. Check the IP address on the VM page

## Expected Results
* Now the VM list only show IP which related to user access. 
* And provide hover message on each displayed IP address
  ![image](https://user-images.githubusercontent.com/29251855/173749441-06fdad41-147a-4703-b19f-eafb1af9f18d.png)
  ![image](https://user-images.githubusercontent.com/29251855/173750324-9f26bcd2-024c-428f-a8bd-2a564c6078f2.png)


