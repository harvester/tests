---
title: Edit a VM from the form to add user data (e2e_fe)
---
1. Add User data to the VM
    - Here is an example of user data config to add a password
    ``
    #cloud-config
    password: password
    chpasswd: {expire: False}
    sshpwauth: True
    ```

1. Save/Create the VM

## Expected Results

1. Machine starts succesfully
1. User data should
    - In YAML
    - In Form
1. Machine should have user password set
