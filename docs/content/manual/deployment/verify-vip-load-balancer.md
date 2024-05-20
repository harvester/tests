---
title: VIP Load balancer verification (e2e_be)
---

## Case DHCP
1. Install Harvester on one Node
    - Install with VIP pulling from DHCP
    - Verify that IP is assigned via DHCP 
2. Add at least one additional node
    - Use VIP address as management address for adding node
3. Finish install of additional nodes
4. Create new VM
5. Connect to VM via web console

## Case Static IP
1. Install Harvester on one Node
    - Install with VIP set statically
    - Verify that IP is assigned correctly
2. Add at least one additional node
    - Use VIP address as management address for adding node
3. Finish install of additional nodes
4. Create new VM
5. Connect to VM via web console

## Expected Results
1. Install of all nodes should complete
2. New nodes should show up in hosts list via web UI at VIP
3. VMs should create
4. Console should open
