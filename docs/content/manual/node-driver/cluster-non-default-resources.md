---
title: Create harvester cluster using non-default CPUs, Memory, Disk
---
1. add a harvester node template
1. The set CPUs, Memory, and Disk values, refer to "Test Data" for other values
1. Use this template to create the corresponding cluster	
## Expected Results
1. The status of the created cluster shows active
1. the status of the corresponding vm on harvester active
1. the information displayed on rancher and harvester matches the template configuration

## Test Data
### Harvester Node Template
### HARVESTER OPTIONS
- Account Access
- Internal Harvester
- Username:admin
- Password:admin
- Instance Options
    ```
    CPUs:4                       Memorys:8
    Disk:50                        Bus:Virtlo
    Image: openSUSE-Leap-15.3.x86_64-NoCloud.qcow2
    Network Name: vlan1 SSH User: opensuse
    ```
### RANCHER TEMPLATE
Name: test-template	