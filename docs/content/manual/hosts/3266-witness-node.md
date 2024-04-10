---
title: Cluster with Witness Node
---

Witness node is a lightweight node only runs **etcd** which is not schedulable and also not for workloads. The main use case is to form a quorum with the other 2 nodes.

Kubernetes need at least 3 **etcd** nodes to form a quorum, so Harvester also suggests using at least 3 nodes with similar hardware spec. This witness node feature aims for the edge case that user only have 2 powerful + 1 lightweight nodes thus helping benefit both cost and high availability.

Related Issues
1. [#3266](https://github.com/harvester/harvester/issues/3266) Support 2 Node / Witness Configuration
1. [#4840](https://github.com/harvester/harvester/issues/4840) [ENHANCEMENT] various witness mode related enhancement



## References
* HLD: https://github.com/harvester/harvester/blob/master/enhancements/20231113-witness-node-support.md
* `rancher-vcluster` addon: https://docs.harvesterhci.io/v1.3/advanced/addons/rancher-vcluster

## Verification Steps
1. Setup a 2 nodes cluster with default installation role
   ![image](https://github.com/harvester/harvester/assets/2773781/f2bb5362-9029-4ee3-a8b5-35af2bc10d5d)
1. Check nodes' role
   * **node-0**: Management node
   * **node-1**: Compute node (quorum yet)
   ![image](https://github.com/harvester/harvester/assets/2773781/53121fb0-89b6-4a7a-8bc7-9db41441b1b8)
1. Setup and join 3rd node with witness role
   ![image](https://github.com/harvester/harvester/assets/2773781/0aa70dba-5d7b-4fcf-935c-1b4fad505ae3)
1. Check nodes' role
   * **node-0**: Management node
   * **node-1**: Management node (Reach quorum, promoted)
   * **node-2**: Witness node
   ![image](https://github.com/harvester/harvester/assets/2773781/1b43dd2c-3b7f-4f2d-8fa6-ffd2f4814b00)
1. Create a VM using default storage class `harvester-longhorn` with some test data
   * Volume should be `Ready` but `Degraded` since replica count is NOT satisfied (expect 3 but only 2 management nodes)
     ![image](https://github.com/harvester/harvester/assets/2773781/d8d7fa01-c3ac-49cb-8afa-08df42c6a2dd)
   * Can NOT migrate VM to witness node
     ![image](https://github.com/harvester/harvester/assets/2773781/0a10825d-91e9-4d1c-993d-89c84708d2fa)
   * Can take snapshot
   * Can take backup
1. Enable `rancher-vcluster`
   * Join Harvester to Rancher
   * Create Nginx deployment
   * Create load balancer for deployment

## Expected Results
1. Restart VM, VM and its data should still fine.
1. Restore snapshot, VM and its data should still fine.
1. Restore backup, VM and its data should still fine.
1. `rancher-vcluster` works.
   ![image](https://github.com/harvester/harvester/assets/2773781/3424370a-3f47-47dd-8225-ee8080df8e01)


## Notes
1. Except manual setup, another approach is harvester setup configuration
   https://docs.harvesterhci.io/v1.3/install/harvester-configuration#installrole