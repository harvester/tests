---
title: Validate network connectivity invalid external VLAN (e2e_be)
---
1. Create a new VM
1. Make sure that the network is set to the external VLAN with bridge as the type and a VLAN ID that isn't valid for your network
1. Ping VM
1. Attempt to SSH to VM

## Expected Results
1. VM should be created
1. You should not be able to ping the VM from an external network
1. You should not be able to SSH to VM
