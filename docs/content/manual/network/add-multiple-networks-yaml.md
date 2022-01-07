---
title: Add multiple Networks via YAML (e2e_be)
---
1. Create a new VM via YAML
1. Add both a management network and an external VLAN network
1. Validate both interfaces exist in the VM
    - `ip link list`
1. Ping the VM from another VM that is only on the management VLAN
1. Ping the VM from an external machine

## Expected Results
1. The VM should create
1. You should see three interfaces listed in VM
1. You should get responses from pinging the VM
1. You should get responses from pinging the VM
