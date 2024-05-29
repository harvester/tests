---
title: 51-Use harvester cloud provider to provision an LB - rke1
---

* Related ticket: [#1396](https://github.com/harvester/harvester/issues/1396) Integration Cloud Provider for RKE1 with Rancher

1. Provision cluster using rke1 with harvester as the node driver
1. Deploy cloud provider from App.
1. Create a deployment with `nginx:latest` image.
1. Create a Harvester load balancer to the pod of above deployment.
1. Verify by clicking the service, if the load balancer is redirecting to the nginx home page.