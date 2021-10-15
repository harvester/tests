---
title: Migrate a VM with multiple networks	
---
1. Create a new VM with
    - one management network in masquerade mode
    - one VLAN network
1. Create a new file on the machine
1. Migrate the VM from one host in the cluster to another
1. Connect via console
1. Check for the file
1. Change the file and save it
1. Verify that you can close and open the file again


## Expected Results
1. File should create correctly
1. VM should go into migrating status
1. VM should go out of migrating status
1. It should show the new node on the host column in the VM list
1. It should have the same IP
1. You should be able to edit and re-open the file