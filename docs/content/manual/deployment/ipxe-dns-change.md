---
title: Change DNS settings on vagrant-pxe-harvester install	
---

- Install using [ipxe-examples](https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-harvester)
- Also change `harvester_network_config.dns_servers` in the `settings.yml` for the vagrant environment before deploy. This will change the DNS in the harvester OS config.
- If you also want to change the DNS for everything in the DHCP scope change `harvester_network_config.dhcp_server.dns_server`.

## Expected Results
1. On completion of the installation, Harvester should provide the management url and show status.
1. SSH into one of the nodes. If you use the default configuration you can use `ssh rancher@192.168.0.30`.
1. When you run `cat /etc/resolv.conf` the changed DNS records should show up