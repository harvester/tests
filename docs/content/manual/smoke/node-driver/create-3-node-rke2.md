---
title: Create a 3 nodes harvester cluster with RKE2 (only with mandatory info, other values stays with default)
---
1. From the Rancher home page, click on Create
1. Select RKE2 on the right and click on Harvester
1. Create the credential to talk with the harvester provider
    - Select your harvester cluster (external or internal)
1. Enter a cluster name
1. Increase machine count to 3
1. Fill the mandatory fields
    - Namespace
    - Image
    - Network
    - SSH User (default ssh user of the chosen image)
1. Click on create to spin the cluster up

## Expected Results
1. The status of the created cluster shows active
1. The status of the corresponding vm on harvester active
1. The 3 nodes should be with the active status