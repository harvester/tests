---
title: 56-Import Harvester to Rancher in airgapped different subnet
---

### Environment Setup
`Note: Harvester and Rancher are under different subnet, can access to each other`

Setup the online harvester
1. Iso or vagrant ipxe install harvester on network with internet connection
1. Enable vlan on `harvester-mgmt`
1. Create virtual machine with name `vlan1` and id: `1`
1. Create ubuntu cloud image from URL
1. Create virtual machine and assign vlan network, confirm can get ip address


Setup the online rancher
1. Install rancher on network with internet connection throug docker command

```
$ sudo docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:v2.6-head
```
1. Login rancher and set access url 

### Test steps

1. Follow steps in `01-Import existing Harvester clusters in Rancher` to import harvester
1. Follow steps in `22-Create RKE2 Kubernetes Cluster` to provision RKE2 cluster


## Expected Results
1. Can import harvester from Rancher correctly 
1. Can access downstream harvester cluster from Rancher dashboard 
1. Can provision at least one node RKE2 cluster to harvester correctly with running status
1. Can explore provisioned RKE2 cluster nodes 
1. RKE2 cluster VM created running correctly on harvester node