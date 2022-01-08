---
title: Add VLAN network (e2e_be)
---
## Environment setup
This should be done on a Harvester setup with at least 2 NICs and at least 2 nodes. This is easily tested in Vagrant
 
## Verification Steps
1. Open settings on a harvester cluster
1. Navigate to the VLAN settings page
1. Click Enabled
1. Check dropdown for NICs and verify that percentage is showing 100% 
1. Add the NIC
1. Click Save
1. Validate that it has updated in settings

## Expected Results
1. You should be able to add the VLAN network device
1. You should see in the settings list that it has your new default NIC
