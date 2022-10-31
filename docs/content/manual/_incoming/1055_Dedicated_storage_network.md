---
title: Dedicated storage network
category: UI
tags: network, settings, volume, p1, integration
---
Ref: https://github.com/harvester/harvester/issues/1055

Verified this feature has been implemented partially.
Mentioned problem in https://github.com/harvester/harvester/issues/1055#issuecomment-1283754519 will be introduced as a enhancement in #2995


Test Information
----
* Environment: **baremetal DL360G9 5 nodes**
* Harvester Version: **master-bd1d49a9-head**
* **ui-source** Option: **Auto**

### Verify Steps:
1. Install Harvester with any nodes
1. Navigate to _Networks -> Cluster Networks/Configs_, create Cluster Network named `vlan`
1. Navigate to _Advanced -> Settings_, edit `storage-network`
1. Select `Enable` then select `vlan` as cluster network, fill in **VLAN ID** and **IP Range**
1. Click Save, warning or error message should displayed.
1. edit `storage-network` again, `mgmt` should not in the drop-down list of `Cluster Network`
1. Navigate to _Networks -> Cluster Networks/Configs_, create Cluster Network named `vlan2`
1. Create `Network Config` for all nodes
1. Navigate to _Advanced -> Settings_, edit `storage-network`
1. Select `Enable` then select `vlan2` as cluster network, fill in **VLAN ID** and **IP Range**
1. Navigate to _Networks -> Cluster Networks/Configs_, delete Cluster Network `vlan2`
1. Warning or error message should displayed
