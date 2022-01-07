---
weight: 1
title: Incoming Test Cases
---
These are some potential new tests for next release.

### v1.0.0 GA Tests
1. RKE1/RKE2 Node driver enhancement [#1174](https://github.com/harvester/harvester/issues/1174), [#1247](https://github.com/harvester/harvester/issues/1247), [#1348](https://github.com/harvester/harvester/issues/1348), [#1373](https://github.com/harvester/harvester/issues/1373), [#1379](https://github.com/harvester/harvester/issues/1379)
1. Rancher import experience [#1330](https://github.com/harvester/harvester/issues/1330)
1. zero downtime upgrade [#1022](https://github.com/harvester/harvester/issues/1022)
1. proxy settings for rke2 and rancher [#1218](https://github.com/harvester/harvester/issues/1218)
1. Volume hot-unplug [#1401](https://github.com/harvester/harvester/issues/1401)
1. cloud config byte limit [#760](https://github.com/harvester/harvester/issues/760)
1. ~~soft reboot/shutdown [#574](https://github.com/harvester/harvester/issues/574)~~ Deferred to v1.0.1
1. VIP accessibility [#1398](https://github.com/harvester/harvester/issues/1398), [#1424](https://github.com/harvester/harvester/issues/1424)
1. Volume scheduling [#1334](https://github.com/harvester/harvester/issues/1334)

### Owner: Unknown
- [BUG] Rancher monitoring stack is crashing on Harvester guest cluster  [#1369](https://github.com/harvester/harvester/issues/1369) owner:unknown p2
- [BUG] Error : can't sync vm backup metadata, err: virtualmachinebackups.harvesterhci.io \"test-backup\" already exists [#1673](https://github.com/harvester/harvester/issues/1673) owner:unknown area/backend, bug

### Owner: David
- [#1476](https://github.com/harvester/harvester/issues/1476) 
  - Add network reachability detection from host for the VLAN network
- [#1433](https://github.com/harvester/harvester/issues/1433) 
  - Allow users to create cloud-config template on the VM creating page
- [#1414](https://github.com/harvester/harvester/issues/1414)
  - Attach unpartitioned NVMe disks to host
- [#1435](https://github.com/harvester/harvester/issues/1435)
  - Better Load Balancer Config of Harvester cloud provider
- [#1454](https://github.com/harvester/harvester/issues/1454)
  - Check can apply the resource quota limit to project and namespace 
- [#1574](https://github.com/harvester/harvester/issues/1574)
  - Check default and customized project and namespace details page 
- [#531](https://github.com/harvester/harvester/issues/531)
  - Check detailed network status in host page
- [#1477](https://github.com/harvester/harvester/issues/1477)
  - Create VM without memory provided
- [#1708](https://github.com/harvester/harvester/issues/1708)
  - Detach volume from virtual machine
- [#1529](https://github.com/harvester/harvester/issues/1529)
  - Disable and enable vlan cluster network
- [#1241](https://github.com/harvester/harvester/issues/1241), [#1382](https://github.com/harvester/harvester/issues/1382), [#1599](https://github.com/harvester/harvester/issues/1599)
  - Disk devices used for VM storage should be globally configurable
- [#1475](https://github.com/harvester/harvester/issues/1475)
  - Download kubeconfig after shutting down harvester cluster
- [#1541](https://github.com/harvester/harvester/issues/1541)
  - Enabling vlan on a bonded NIC on vagrant install
- [#1167](https://github.com/harvester/harvester/issues/1167)
  - Host list should display the disk error message on failure
- [#1218](https://github.com/harvester/harvester/issues/1218), [#1012](https://github.com/harvester/harvester/issues/1012)
  - Http proxy setting on harvester 
- [#1644](https://github.com/harvester/harvester/issues/1644), [#1588](https://github.com/harvester/harvester/issues/1588)
  - Manual upgrade from 0.3.0 to 1.0.0
- [#1316](https://github.com/harvester/harvester/issues/1316)
  - Move Longhorn storage to another partition
- [#1501](https://github.com/harvester/harvester/issues/1501)
  - Nodes with cordoned status should not be in VM migration list
- [#1455](https://github.com/harvester/harvester/issues/1455), [#1449](https://github.com/harvester/harvester/issues/1449)
  - Provision RKE2 cluster with resource quota configured
- [#1330](https://github.com/harvester/harvester/issues/1330)
  - Rancher import harvester enhancement
- [#1493](https://github.com/harvester/harvester/issues/1493)
  - Recover cordon and maintenace node after harvester node machine reboot
- [#1014](https://github.com/harvester/harvester/issues/1014)
  - Set maintenance mode on the last available node shouldn't be allowed
- [#1401](https://github.com/harvester/harvester/issues/1401)
  - Support volume hot plug live migrate
  - Support Volume Hot Unplug
- [#1464](https://github.com/harvester/harvester/issues/1464)
  - Switch the vlan interface of harvester node
- [#1465](https://github.com/harvester/harvester/issues/1465)
  - toggle harvester node driver with the harvester global flag
- [#1620](https://github.com/harvester/harvester/issues/1620)
  - Use template to create cluster through virtualization management
- [#1424](https://github.com/harvester/harvester/issues/1424)
  - VIP configured in a VLAN network should be reached 


### Owner: Lanfon, Not added issues
- [#1387](https://github.com/harvester/harvester/issues/1387), VM related but can't be reproduced
- [#1583](https://github.com/harvester/harvester/issues/1583), bug of `yip` tool, not harvester
- [#1263](https://github.com/harvester/harvester/issues/1263), bug of Longhorn#3315, fixed after Longhorn v1.2.2
- [#1405](https://github.com/harvester/harvester/issues/1405), install config, typo on document
- [#1431](https://github.com/harvester/harvester/issues/1431), install config, lack document
- [#1453](https://github.com/harvester/harvester/issues/1453), UI's basic operation on VM page
- [#1269](https://github.com/harvester/harvester/issues/1269), UI's basic operation on Image page
- [#1612](https://github.com/harvester/harvester/issues/1612), regression Hosts No.1
- [#1253](https://github.com/harvester/harvester/issues/1253), regression Hosts No.1
- [#1376](https://github.com/harvester/harvester/issues/1376), regression VM No.71-76
- [#1386](https://github.com/harvester/harvester/issues/1386), regression VM No.28,53
- [#1376](https://github.com/harvester/harvester/issues/1376), regression VM No.71-76
- [#1360](https://github.com/harvester/harvester/issues/1360), regression Backup and Restore Negative No.4,5,14,15
- [#1304](https://github.com/harvester/harvester/issues/1304), regression UI No.5