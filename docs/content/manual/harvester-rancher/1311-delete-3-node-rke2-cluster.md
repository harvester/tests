---
title: Delete 3 node RKE2 cluster
---

* Related issues: [#1311](https://github.com/harvester/harvester/issues/1311) Deleting a cluster in rancher dashboard doesn't fully remove

## Verification Steps

1. Create 3 node RKE2 cluster on Harvester through node driver with Rancher
1. Wait fo the nodes to create, but not fully provision
1. Delete the cluster
1. Wait for them to be removed from Harvester
1. Check Rancher cluster management

## Expected Results
1. Cluster should be removed from Rancher
1. VMs should be removed from Harvester