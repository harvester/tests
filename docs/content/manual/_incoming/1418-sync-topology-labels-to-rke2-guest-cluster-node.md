---
title: Sync harvester node's topology labels to rke2 guest-cluster's node
---
* Related issues: [#1418](https://github.com/harvester/harvester/issues/1418) Support topology aware scheduling of guest cluster workloads

## Verification Steps
1. Add [topology labels](https://kubernetes.io/docs/reference/labels-annotations-taints/#topologykubernetesioregion)(`topology.kubernetes.io/region`, `topology.kubernetes.io/zone`) to the Harvester node:
    - In Harvester UI, select `Hosts` page.
    - Click hosts' `Edit Config`.
    - Select `Labels` page, click `Add Labels`.
    - Fill in, eg, Key: `topology.kubernetes.io/zone`, Value: `zone1`.

2. Create harvester guest-cluster from rancher-UI.
3. Wait for the guest-cluster to be created successfully and check if the guest-cluster node labels are consistent with the harvester nodes.
    - In Rancher UI, select guest cluster.
    - Select `Nodes`.
    - Click each node, and check if contains labels.