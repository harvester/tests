---
title: Config sftp dynamically
---

* Related issues: [#4480](https://github.com/harvester/harvester/issues/4480) [ENHANCEMENT] config sftp dynamically


## Category: 
* Deployment

## Verification Steps
1. Use ipxe-example to provision Harvester
1. Add the following sshd config to the config-create.yaml and config-join.yaml of Harvester configuration file
    ```
    os:
    sshd:
    sftp: true
    ```
1. Provision the 3 nodes Harvester cluster
1. After provisioning or upgrade complete, ssh to the management and worker node
1. Check the file exists
    ```
    sudo tail -n5 /etc/ssh/sshd_config
    cat /etc/ssh/sshd_config.d/sftp.conf
    ```
1. Use sftp to connect to Harvester, check the connection works
    ```
    sftp rancher@192.168.0.131
    ```

## Expected Results
1. Fresh install: on create node and compute node machine, we can sftp connect to the node and find the corresponding file
    ```
    harvester@localhost:~/Harvester/ipxe-examples/vagrant-pxe-harvester> ssh rancher@192.168.0.131
    Password: 
    Last login: Wed Jan 10 05:42:44 2024 from 192.168.0.1
    rancher@harvester-node-0:~> pwd
    /home/rancher
    rancher@harvester-node-0:~> vim test.txt
    rancher@harvester-node-0:~> exit
    logout
    Connection to 192.168.0.131 closed.
    harvester@localhost:~/Harvester/ipxe-examples/vagrant-pxe-harvester> sftp rancher@192.168.0.131
    Password: 
    Connected to 192.168.0.131.
    sftp> ls -al
    drwxr-xr-x    3 rancher  rancher      4096 Jan 10 05:48 .
    drwxr-xr-x    3 root     root         4096 Jan 10 03:56 ..
    -rw-------    1 rancher  rancher        92 Jan 10 05:48 .bash_history
    drwx------    2 rancher  rancher      4096 Jan 10 03:56 .ssh
    -rw-r-----    1 rancher  rancher         5 Jan 10 05:48 test.txt
    sftp> get test.txt test.txt 
    Fetching /home/rancher/test.txt to test.txt
    /home/rancher/test.txt                                                                                                      100%    5     5.3KB/s   00:00
    ```
1. After reboot machine, the sftp service and corresponding file exists 
    ```
    harvester@localhost:~/Harvester/ipxe-examples/vagrant-pxe-harvester> ssh rancher@192.168.0.131
    Password: 
    $ sudo tail -n5 /etc/ssh/sshd_config
    AllowAgentForwarding no
    X11Forwarding no
    AllowTcpForwarding no
    MaxAuthTries 3
    Include /etc/ssh/sshd_config.d/*.conf
    rancher@harvester-node-2:~> exit
    logout
    Connection to 192.168.0.131 closed.
    harvester@localhost:~/Harvester/ipxe-examples/vagrant-pxe-harvester> sftp rancher@192.168.0.131
    Password: 
    Connected to 192.168.0.131.
    ```
1. After upgrade, the sftp service and corresponding file exists
    ```
    rancher@harvester-node-0:~> cat /etc/ssh/sshd_config.d/sftp.conf
    Subsystem	sftp	/usr/lib/ssh/sftp-server
    rancher@harvester-node-0:~> exit
    logout
    Connection to 192.168.0.131 closed.
    davidtclin@localhost:~/Documents/Project_Repo/ipxe-examples/vagrant-pxe-harvester> sftp rancher@192.168.0.131
    Password: 
    Connected to 192.168.0.131.
    sftp>
    ```