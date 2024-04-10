---
title: Node pool anti-affinity rules
---

* Related issues: [#4588](https://github.com/harvester/harvester/issues/4588) [BUG] Node pool anti-affinity rules are not working as expected
* Related issues: [#4898](https://github.com/harvester/harvester/issues/4898) [backport v1.2] [BUG] Node pool anti-affinity rules are not working as expected

## Category: 
* Virtual Machines

## Verification Steps
1. Provision the 3 nodes Harvester cluster
1. Provision the latest Rancher instance
1. Import Harvester to Rancher
1. Open the node driver page in Rancher dashboard
1. Ensure the Harvester node driver version > 0.6.6
1. Add label `topology.kubernetes.io/zone` and a different zone value, say `zone1`, `zone2`, `zone3` is added to each node of the harvester cluster
{{< image "images/virtual-machines/4588-host-topology-zone.png" >}}
1. Provision the downstream RKE2 guest cluster with 3 machine counts
1. Specify the VM `anti-affinity` scheduling rule:
{{< image "images/virtual-machines/4588-vm-anti-affinity.png" >}}
1. Verify the VM's will be spread across the three different nodes
1. Check the yaml content of each VM,
1. Each VM launched will have an additional label added.
1. The anti-affinity rule on the VM will leverage this label to ensure VM's are spread across in the cluster

1. Corden one of the node on Harvester host page
1. Repeat step 7 - 12

## Expected Results
* VM's will be spread across the three different nodes
{{< image "images/virtual-machines/4588-vm-spread-across-nodes.png" >}}

* Each VM launched will have an additional label added.
* The anti-affinity rule set on the label of vm in the yaml content 
{{< image "images/virtual-machines/4588-yaml-anti-affinity.png" >}}

* If Node 2 cordened, none of the VM would be scheduled on that node
{{< image "images/virtual-machines/4588-vm-cannot-schedule-specific-node.png" >}}

* The anti-affinity rule set on the label of vm in the yaml content
{{< image "images/virtual-machines/4588-yaml-negative-anti-affinity.png" >}}