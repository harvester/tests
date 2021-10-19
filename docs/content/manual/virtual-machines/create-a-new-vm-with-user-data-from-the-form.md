---
title: Create a new VM with User Data from the form	
---
1. Add User data to the VM
- Here is an example of user data config to add a password
        ```
        #cloud-config
        password: password
        chpasswd: {expire: False}
        sshpwauth: True
        Save/Create the VM
        ```
## Expected Results
1. Machine starts succesfully
1. User data should exist
    - In YAML
    - In Form
1. Machine should have user password set