---
title: Check IPv4 static method in ISO installer
---

* Related issues: [#2796](https://github.com/harvester/harvester/issues/2796) [BUG] configure network failed if use static mode

  
## Category: 
* Newtork
* Harvester Installer

## Verification Steps
1. Use latest ISO to install
1. Enter VLAN field with 
    - empty
    - 1
    - 1000
1. choose static method
1. fill other fields
1. press enter to the next page
1. no error found, and show DNS config page

## Expected Results
During Harvester ISO installer 
We can configure VLAN network on the static mode with the following settings: 
1. No error message blocked
1. Can proceed to dns config page 

