---
title: Verify Enabling maintenance mode	
---
1. Navigate to the Hosts page and select the node
2. Click Maintenance Mode

## Expected Results
1. The existing VM should get migrated to other nodes.
2. Verify the CRDs to see the maintenance mode is enabled.

### Comments
1. Needs other test cases to be added
2. If VM migration fails
3. How does live migration work
4. What happens if there are no schedulable resources on nodes
    - Check CRDs on hosts
        - On going into maintenance mode
        - kubectl get virtualmachines --all-namespaces
    - Kubectl get virtualmachines/name -o yaml
        - On coming out of maintenance mode
        - kubectl get virtualmachines --all-namespaces
5. Kubectl get virtualmachines/name -o yaml
    - Check that maintenance mode host isn't schedulable
        - Fully provision all nodes and try to create a VM
6. It should fail
    - Migration with maintenance mode
    - What if migration gets stuck, can you cancel
    - VMs going to different hosts
    - Canceling maintenance mode
    - P1 
        - Put in maintenance mode
        - Check migration of VMs
        - Check status of VMs
        - modify filesystem on VMs
        - Check status of host
        - Take host out of maintenance mode
        - Check status of host
        - Migrate VMs back to host
        - Check filesystem
        - Create new VMs on host
        - Check status of VMs
