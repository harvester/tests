---
title: Create Single instances of the vm with Windows Image (e2e_be)
---
1. Create vm using the external path for ISO image.
1. In user data mention the below to access the vm. 
```
#cloud-config
password: password
chpasswd: {expire: False}
sshpwauth: True
```
1. Create the vm and wait for vm to start.


## Expected Results
1. VM should come up and start with same config.
