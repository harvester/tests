---
title: Change DNS servers while installing
---

* Related issues: [#1590](https://github.com/harvester/harvester/issues/1590) Harvester installer can't resolve hostnames

## Known Issues
When supplying multiple ip=... kernel cmdline arguments, only one of them will be configured by dracut, therefore only the configured interface would have ifcfg generated. So for now, we can't support multiple ip=... kernel cmdline arguments

## Verification Steps
1. Because configuring the network of the installation environment only works with PXE installation, you could use ipxe-examples/vagrant-pxe-harvester/ to set it up. Be sure you can run setup_harvester.sh without any problem.

1. Run setup_harvester.sh, then interrupt it using Ctrl-C after the PXE server is ready, as we need to update the kernel parameters passing to the Nodes from the PXE server.

    - Note: You could wait until the step TASK [wait for Harvester Node 192.168.0.30 to get ready] to interrupt it, then run:
    ```
    vagrant destroy harvester-node-0
    ```
    to remove the first Node VM

1. SSH into the PXE server: `$ vagrant ssh pxe_server`

1. Edit the file /var/www/harvester/02:00:00:0d:62:e2 and add kernel parameters nameserver=1.1.1.1 to the end of the line imgargs:
    ```
    ...
    imgargs harvester-vmlinuz-amd64 initrd=harvester-initrd-amd64 ... nameserver=1.1.1.1
    ...
    ```
    - Note: The file `/var/www/harvester/02:00:00:0d:62:e2` provides booting information only to the first Node because the file name is the MAC address of the first Node. You could modify the other two files which also have file name mapped to the MAC address of the second and the third Nodes under /var/www/harvester/ to pass them the kernel parameters.

1. Now you can start provisioning the first Node by executing setup_harvester.sh again.

1. Open the VM display. When the installation process started, press Ctrl-Alt-F2 to switch to another virtual console and login with rancher/rancher so we could verify the network config.

1. Check /etc/resolv.conf and verify it has the following line:
    ```
    nameserver 1.1.1.1
    ```
    which is the nameserver (DNS) we passed using kernel parameters from the PXE server.

1. You could further test more cases such as multiple nameserver=<IP> parameters and configure a static IP with ip= parameter. Check dracut.cmdline and look for ip and nameserver parameters for how to configure network of the installation environment.

    - Note: If you want to test ip=... parameter, do notice that we already have one such parameter ip=ens5:dhcp in the original /var/www/harvester/02:00:00:0d:62:e2. For now we only support a single ip= parameter so remove it before you added a new one.

    - Note: If you have configured a static IP, it's highly possible that the setup_harvester.sh will timeout on task wait for Harvester Node <IP> to get ready, because it's expecting a certain IP for connecting to the Node and you've changed it. Despite the script failed, the installation should be completed without any problem.


## Expected Results
1. The nameserver should show
    - Note: make sure that you check before it automatically reboots as part of the install


