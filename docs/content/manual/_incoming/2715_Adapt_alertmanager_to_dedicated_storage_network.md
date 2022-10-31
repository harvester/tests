---
title: Adapt alertmanager to dedicated storage network
category: UI
tags: dashboard, network, settings, volume, p1, integration
---
Ref: https://github.com/harvester/harvester/issues/2715


### criteria
PVCs (alertmanager/grafana/Prometheus) will attach back after dedicated storage network switched.

### Verify Steps:
1. Install Harvester with any nodes
1. Navigate to _Networks -> Cluster Networks/Configs_, create Cluster Network named `vlan`, create **Network Config** for all nodes
1. Navigate to _Advanced -> Settings_, edit `storage-network`
1. Select `Enable` then select `vlan` as cluster network, fill in **VLAN ID** and **IP Range**
1. Wait until error message (displayed under _storage network_ setting) disappeared
1. Navigate to _Monitoring & Logging -> Monitoring -> Configuration_
1. Dashboard of Prometheus Graph, Grafana and Altertmanager should able to access, and should contain old data.
