---
title: 58-Negative-Fully power cycle harvester node machine should recover RKE2 cluster
---

 * Related issue: [#1561](https://github.com/harvester/harvester/issues/1561) Fully shutdown then power on harvester node machine can't get provisioned RKE2 cluster back to work

 * Related issue: [#1428](https://github.com/harvester/harvester/issues/1428) rke2-coredns-rke2-coredns-autoscaler timeout 

## Environment Setup
* The network environment must have vlan network configured and also have DHCP server prepared on your testing vlan

## Verification Step
1. Prepare a 3 nodes harvester cluster (provo bare machine)
1. Enable virtual network with harvester-mgmt
1. Create vlan1 with id `1`
1. Import harvester from rancher and create cloud credential
1. Provision a RKE2 cluster with vlan `1`
1. Wait for build up ready
1. Shutdown harvester node 3 
1. Shutdown harvester node 2
1. Shutdown harvester node 1
1. Wait for 20 minutes
1. Power on node 1, wait 10 seconds
1. Power on node 2, wait 10 seconds
1. Power on node 3
1. Wait for harvester startup complete
1. Wait for RKE2 cluster back to work
1. Check node and VIP accessibility
1. Check the rke2-coredns pod status `kubectl get pods --all-namespaces | grep rke2-coredns`

## Expected Results
1. RKE2 cluster on harvester `can recover` to `Active` status

1. Can access dashboard by VIP
1. Can access each node IP
1. rke2-coredns pods running correctly

```harvester-node03-1215:/home/rancher # kubectl get pods --all-namespaces | grep rke2-coredns
kube-system helm-install-rke2-coredns-74nsk 0/1 Completed 0 176m
kube-system rke2-coredns-rke2-coredns-5679c85bbb-5qrmm 1/1 Running 1 175m
kube-system rke2-coredns-rke2-coredns-5679c85bbb-zxpf8 1/1 Running 1 147m
kube-system rke2-coredns-rke2-coredns-autoscaler-6889866896-l42m8 1/1 Running 1 175m
```
