---
title: Configure VLAN interface on ISO installer UI
---

* Related issues: [#1647](https://github.com/harvester/harvester/issues/1647) [FEATURE] Support configuring a VLAN at the management interface in the ISO installer UI

  
## Category: 
* Network
* Harvester Installer

## Environment Setup
1. Prepare a `No` VLAN network environment 
1. Prepare a `VLAN` network environment

## Verification Steps
1. Boot Harvester ISO installer
1. Set VLAN id or keep empty
1. Keep installing
1. Check can complete installation
1. Check harvester has network connectivity 

## Test Plan Matrix

### Create mode
#### No VLAN 
1. DHCP VIP + DHCP node ip
1. DHCP VIP + Static node ip
1. static VIP + DHCP node ip
1. static VIP + Static node ip

#### VLAN 
1. DHCP VIP + DHCP node ip
1. DHCP VIP + Static node ip
1. static VIP + DHCP node ip
1. static VIP + Static node ip


### Join mode
#### No VLAN 
1. DHCP VIP + DHCP node ip
1. DHCP VIP + Static node ip
1. static VIP + DHCP node ip
1. static VIP + Static node ip

#### VLAN 
1. DHCP VIP + DHCP node ip
1. DHCP VIP + Static node ip
1. static VIP + DHCP node ip
1. static VIP + Static node ip

## Expected Results
1. Check can complete installation
1. Check harvester has network connectivity
1. `ip a show dev mgmt-br [VLAN ID]` has IP
1. e.g ip a show dev mgmt-br.100
