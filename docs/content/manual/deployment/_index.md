---
title: Deployment tests for harvester
---
# Installation
- ISO installation - Get the images from https://github.com/harvester/harvester/releases
- PXE boot installation - https://docs.harvesterhci.io/v0.2/install/pxe-boot-install/
- Rancher app deployment for development purpose
## How to test Harvester Master
1. For harvester-installer tests, we can download the latest ISO from https://releases.rancher.com/harvester/master/harvester-amd64.iso that is built with a daily CRON job.
2. For the harvester server, just replace the harvester image with `master-head` on the harvester-system namespace, if u have only a single node u can delete the replicaset to restart the pod e.g, (kubectl delete rs harvester-xxxxx) 
    - kubectl patch deployment harvester -p '{"spec": {"template": {"spec": {"containers": [{"image:": "rancher/harvester:master-head" }]}}}' -n harvester-system 
    - check and apply the latest CRDs from the master branch if needed.  https://github.com/harvester/harvester/tree/master/deploy/charts/harvester/crds 
