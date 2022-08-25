---
title: Terraformer import KUBECONFIG
---

* Related issues: [#2604](https://github.com/harvester/harvester/issues/2604) [BUG] Terraformer imported VLAN always be 0

## Category: 
* Terraformer

## Verification Steps
1. Install Harvester with any nodes
1. Login to dashboard, navigate to: Advanced/Settings -> then enabledvlan`
1. Navigate to Advanced/Networks and Create a Network which Vlan ID is not 0
1. Navigate to Support Page and Download KubeConfig file
1. Initialize a terraform environment, download Harvester Terraformer
1. Execute command `terraformer import harvester -r network` to generate terraform configuration from the cluster
1. Generated file `generated/harvester/network/network.tf` should exists
1. VLAN and other settings should match

## Expected Results
1. vlan_id should be the same as the import cluster.