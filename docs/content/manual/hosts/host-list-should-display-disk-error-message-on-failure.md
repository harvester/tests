---
title: Host list should display the disk error message on failure
---

 * Related issue: [#1167](https://github.com/harvester/harvester/issues/1167) Host list should display the disk error message on table

## Category: 
* Storage

## Verification Steps
1. Shutdown existing node vm machine
1. Run "qemu-img create" command to make a nvme.img
1. Edit quem/kvm xml setting to attach the nvme image
1. Start VM
1. Open hostpage and edit your target node config
1. Add the new nvme disk 
1. Shutdown VM
1. Remove the attach device setting in VＭ xml file
1. Start VM
1. Open Host page, the targe node will show warning with unready and unscheduable disk exists

## Expected Results
1. If host encounter disk ready or schedule failure, on host page the "disk state" will show **warning**
With a hover tip "**Host have unready or unschedulable disks"**

![image](https://user-images.githubusercontent.com/29251855/138687164-877422a0-d33b-4e26-9c0b-d52b8f4e6995.png)

1. Can create load balancer correctly with health check setting