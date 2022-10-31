---
title: Instance metadata variables are not expanded
category: UI
tags: VM, p1, functional
---
Ref: https://github.com/harvester/harvester/issues/2342

![image](https://user-images.githubusercontent.com/5169694/177121301-f30bf8ec-0a70-4549-b11b-895161ee30ad.png)


### Verify Steps:
1. Install Harvester with any nodes
1. Create Image for VM creation
1. Create VM with following _CloudConfig_
```yaml
## template: jinja
#cloud-config
package_update: true
password: password
chpasswd: { expire: False }
sshpwauth: True
write_files:
  - content: |
      #!/bin/bash
      vmName=$1
      echo "VM Name is: $vmName" > /home/cloudinitscript.log
    path: /home/exec_initscript.sh
    permissions: '0755'
runcmd:
  - - systemctl
    - enable
    - --now
    - qemu-guest-agent.service
  - - echo
    - "{{ ds.meta_data.local_hostname }}"
  - - /home/exec_initscript.sh
    - "{{ ds.meta_data.local_hostname }}"
packages:
  - qemu-guest-agent
```

1. login to the VM
    - file `/home/exec_initscript.sh` should exists
    - file `/home/cloudinitscript.log` should exists
    - execute `cat /home/cloudinitscript.log`, VM name should be the same as the VM.
