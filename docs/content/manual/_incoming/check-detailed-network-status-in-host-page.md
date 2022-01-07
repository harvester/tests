---
title: check detailed network status in host page
---

* Related issues: [#531](https://github.com/harvester/harvester/issues/531) Better error messages when misconfiguring multiple nics

## Category: 
* Host

## Verification Steps
1. Enable vlan cluster network setting and set a default network interface
1. Wait a while for the setting take effect on all harvester nodes
1. Click nodes on host page 
1. Check the network tab

## Expected Results
On the Host view page, now we can see detailed network status including `Name`, `Type`, `IP Address`, `Status` etc..
![image](https://user-images.githubusercontent.com/29251855/141070311-55ec4382-d777-4289-91c7-cebe81db3356.png)

1. Check all network interface can display 
1. Check the `Name`, `Type`, `IP Address`, `Status` display correct values


