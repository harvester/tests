---
title: Delete management network via YAML
---
1. On a VM with both an external VLAN and a management VLAN delete the management network via YAML
1. Validate interface was removed with
    - `ip link list`
1. Ping the VM from another VM that is only on the management VLAN
1. Ping the VM from an external machine

## Expected Results
1. The VM should update and reboot
1. You should only see one interface (and the loopback) in the list
1. You should not be able to ping the VM on the management network
1. You should get responses from the VM