---
title: VMs can't start if a node contains more than ~60 VMs
category: console
tag: VM, p1, acceptance
---
Ref: https://github.com/harvester/harvester/issues/2722

![image](https://user-images.githubusercontent.com/5169694/192251104-7a53a1a9-260d-4e90-aade-1b3e7c11cc52.png)


### Verify Steps:
1. Install Harvester with any nodes
1. Login to console, execute `sysctl -a | grep aio`, the value of `fs.aio-max-nr` should be `1048576`
1. Update the value by executing:
```bash
mkdir -p /usr/local/lib/sysctl.d/
cat > /usr/local/lib/sysctl.d/harvester.conf <<EOF
fs.aio-max-nr = 61440
EOF
sysctl --system
```
1. Execute `sysctl -a | grep aio`, the value of `fs.aio-max-nr` should be `61440`
1. Reboot the node then execute `sysctl -a | grep aio`, the value of `fs.aio-max-nr` should still be `61440`
1. Create an image for VM creation
1. Create 60 VMs and schedule on the node which updated `fs.aio-max-nr`
1. Update `fs.aio-max-nr` to `1048576` in `/usr/local/lib/sysctl.d/harvester.conf` and execute `sysctl --system`
1. VMs should started successfully or Stopping with error message `Too many pods`
