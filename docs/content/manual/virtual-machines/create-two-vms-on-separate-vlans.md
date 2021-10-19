---
title: Create two VMs on separate VLANs	
---
1. Create/edit VM/VMs with the appropriate VLAN
1. Change VLAN for VM if appropriate

## Expected Results
1. VM should create successfully
1. Appropriate VLAN should show
    - In config
    - in YAML
1. VMs should NOT be able to connect on network
    - verify with ping/ICMP
    - verify with SSH
    - verify with telnet over port 80 if there's a web server