---
title: Add a custom "Storage Driver"
---
1. add a harvester node template
1. Refer to the "Test Data" value setting.
1. Use this template to create the corresponding cluster

## Expected Results
1. The status of the created cluster shows active
1. the status of the corresponding vm on harvester active
1. the information displayed on rancher and harvester matches the template configuration
1. Go to node, execute "docker info", check the Storage Driver setting is overlay

## Test Data
### Harvester Node Template
### HARVESTER OPTIONS
- Account Access
- Internal Harvester
- Username:admin
- Password:admin
- Instance Options
    ```
    CPUs:2                       Memorys:4
    Disk:40                        Bus:Virtlo/SATA/SCSI
    Image: openSUSE-Leap-15.3.x86_64-NoCloud.qcow2
    Network Name: vlan1 SSH User: opensuse
    ```
### RANCHER TEMPLATE
Name: test-template
Engine Option:
Storage Driver: overlay2