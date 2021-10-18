---
title: Import External Harvester
---
With Rancher < 2.6:
1. Deploy the rancher and harvester clusters separately
1. In the rancher, add a harvester node template
1. Select "External Harvester", and refer to "Test Data" for other value settings.
1. Use this template to create the corresponding cluster
With Rancher 2.6:
1. Home page / Import Existing / Generic
1. Add cluster name and click on Create
1. Follow the registration steps

## Expected Results
1. The status of the created cluster shows active
1. The status of the corresponding vm on harvester active
1. The information displayed on rancher and harvester matches the template configuration

## Test Data
### Harvester Node Template
### HARVESTER OPTIONS
- Account Access
- External Harvester
- Host: <ipAddress> Port: 443
- Username:admin
- Password:admin
- Instance Options
    ```
    CPUs:2                       Memorys:4
    Disk:40                        Bus:Virtlo
    Image: openSUSE-Leap-15.3.x86_64-NoCloud.qcow2
    Network Name: vlan1 SSH User: opensuse
    ```
### RANCHER TEMPLATE
Name: test-template	