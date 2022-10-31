---
title: Harvester uses active-backup as the default bond mode
category: console
tags: installer, p1, functional
---
Ref: https://github.com/harvester/harvester/issues/2472

![image](https://user-images.githubusercontent.com/5169694/184838334-a723f066-8eef-4cbc-ab66-6e02b758823d.png)
![image](https://user-images.githubusercontent.com/5169694/184839241-3702fa7c-950e-4b51-8c18-d29d4121f848.png)


### Verify Steps:
1. Install Harvester via ISO
1. The default **Bond Mode** should select `active-backup`
1. Ater installed with `active-backup` mode, login to console
1. Execute `cat /etc/sysconfig/network/ifcfg-harvester-mgmt`, **BONDING_MODULE_OPTS** should contains `mode=active-backup`
