---
title: Create a new VM and add Install guest agent option (e2e_be)
---
1. Add install Guest Agent Option
1. Save/Create VM
1. Validate that qemu-guest-agent was installed
    - You can do this on ubuntu with the command `dpkg -l | grep qemu`

## Expected Results
1. Machine starts successfully
1. Guest Agent Option shows 
    - In YAML
    - In Form
1. Guest Agent is installed
