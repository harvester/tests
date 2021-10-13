---
title: Verify Configuring via HTTP URL	
---
1. Provide the remote Harvester config, you can find an example of the config I'm using in the deployment test plan description

## Expected Results
1. Check that all values are taking into account
    - If you are using my config file, check:
    - the node must be off after the installation
    - the nvme and kvm modules are loaded
    - the file /etc/test.txt exists with the correct rights
    - the systcl values
    - the env variable test_env should exist
    - dns configured in /etc/resolv.conf 
    - ntp configured in /etc/systemd/timesyncd.conf
2. Check the config file here: /oem/harvester.config
