---
title: Verify "Add Node Pool"
---
1. Create a cluster of 3 nodes, One node with etcd, Control Plane, Worker, the other two with Worker
1. The cluster is created successfully, use the command `kubectl get node` to view the node roles

## Expected Results
1. The status of the created cluster shows active
1. show the 3 created node status running in harvester's vm list
1. the information displayed on rancher and harvester matches the template configuration
1. Check that the node role is correct