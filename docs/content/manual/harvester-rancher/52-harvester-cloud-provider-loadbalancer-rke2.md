---
title: 52-Use harvester cloud provider to provision an LB - rke2
---

1. Provision cluster using rke2 with harvester as the node driver
1. Enable the cloud driver for `harvester` while provisioning the cluster
1. Create a deployment with `nginx:latest` image.
1. Create a Harvester load balancer to the pod of above deployment.
1. Verify by clicking the service, if the load balancer is redirecting to the nginx home page.