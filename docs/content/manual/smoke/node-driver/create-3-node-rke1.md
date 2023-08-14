---
title: Create a 3 nodes harvester cluster with RKE1 (only with mandatory info, other values stays with default)
---
1. From the Rancher home page, click on Create
1. Select RKE1 on the right and click on Harvester
1. Enter a cluster name
1. Give a prefix name for the VMs
1. Increase count to 3 nodes
1. Check etcd, Control Plane and Worker boxes
1. Select or create a node template if needed
    - Click on Add node template
    - Create credentials by selecting your harvester cluster
    - Fill the instance option fields, pay attention to correctly write the default ssh user of the chosen image in the SSH user field
    - Give a name to the rancher template and click on Create
1. Click on create to spin the cluster up

## Expected Results
1. The status of the created cluster shows active
1. The status of the corresponding vm on harvester active
1. The 3 nodes should be with the active status