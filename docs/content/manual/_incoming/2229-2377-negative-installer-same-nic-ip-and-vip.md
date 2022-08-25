---
title: Negative Harvester installer input same NIC IP and VIP
---

* Related issues: [#2229](https://github.com/harvester/harvester/issues/2229) [BUG] input nic ip and vip with same ip address in Harvester-Installer
* Related issues: [#2377](https://github.com/harvester/harvester/issues/2377) [Backport v1.0.3] input nic ip and vip with same ip address in Harvester-Installer

## Category: 
* Installation

## Verification Steps
1. Boot into ISO installer
1. Specify same IP for NIC and VIP

## Expected Results
1. Error message is displayed
![image](https://user-images.githubusercontent.com/83787952/178049998-e4eec9fe-d687-4efc-9618-940432d37a3d.png)