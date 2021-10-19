---
title: Cluster add labs
---
1. add a harvester node template
1. Refer to the "Test Data" value setting.
1. Use this template to create the corresponding cluster	

## Expected Results
1. Use the command "kubectl get node --show-labels" to see the success of the added tabs
1. Go to the node details page of UI, click the "Edit Node" button, and check Labels

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