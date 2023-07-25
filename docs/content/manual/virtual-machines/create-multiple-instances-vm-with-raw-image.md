---
title: Create multiple instances of the vm with raw image (e2e_be_fe)
---
1. Create images using the external path for cloud image.
1. In user data mention the below to access the vm.
1.

```
#cloud-config
password: password
chpasswd: {expire: False}
sshpwauth: True
```

1. Create the 3 vms and wait for vm to start.

## Expected Results

1. 3 vm should come up and start with same config.
1. Observe the time taken for the system to start the vms.
1. Observe the pattern of the vms get allocated on the nodes. Like how many vm on each nodes are created. Is there a pattern?
