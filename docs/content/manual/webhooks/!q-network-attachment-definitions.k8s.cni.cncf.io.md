---
title: network-attachment-definitions.k8s.cni.cncf.io
---
### GUI
1. Enable VLAN network in settings
1. Create a network with VLAN 5 and assume its name is my-network.
1. Create another network with VLAN 5: it should fails with:
admission webhook "[validator.harvesterhci.io](http://validator.harvesterhci.io/)" denied the request: VLAN ID 5 is already allocated
1. Create a VM on VLAN 5, delete network my-network and it should fail with:
admission webhook "[validator.harvesterhci.io](http://validator.harvesterhci.io/)" denied the request: network my-network is still used by vm(s): vm-test in a modal
## Expected Results
### GUI
Unsure of desired behavior. Checking and will update.