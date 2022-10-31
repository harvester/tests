---
title: Support configuring a VLAN at the management interface in installer config
category: console
tags: installer, p1, functional
---
Ref: https://github.com/harvester/harvester/issues/1390, https://github.com/harvester/harvester/issues/1647

![image](https://user-images.githubusercontent.com/5169694/192803102-5062546d-ec36-4ecc-a1f3-4e6ec6c7a620.png)


### Verify Steps:
1. Install Harvester with any nodes from PXE Boot with configurd vlan with `vlan_id`
1. Harvester should installed successfully
1. Login to console, execute `ip a s dev mgmt-br.<vlan_id>` should have IP and accessible
1. Dashboard should be accessible
