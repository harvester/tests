---
title: Check DNS on install with Github SSH keys
---
* Related issues: [#1903](https://github.com/harvester/harvester/issues/1903) DNS server not available during install

## Verification Steps
### Without PXE
1. Start a new install
2. Set DNS as `8.8.8.8`
3. Add in github SSH keys
4. Finish install
5. SSH into node with SSH keys from github (`rancher@hostname`)
6. Verify login was successful

### With PXE
1. Got vagrant setup from https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-harvester
2. Changed `settings.yml` DHCP config and added `dns: 8.8.8.8`
```
dhcp_server:
    ip: 192.168.0.254
    subnet: 192.168.0.0
    netmask: 255.255.255.0
    range: 192.168.0.50 192.168.0.130
    dns: 8.8.8.8
    https: false
```
Also changed `ssh_authorized_keys` and commented out default SSH key and added username for github
```
  ssh_authorized_keys:
    # Vagrant default unsecured SSH public key
    # - ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ== vagrant insecure public key
    - github:username
```
3. Ran `sudo setup_harvester.sh`
4. Waited for install to finish
5. Verified I could SSH into the VIP at `192.168.0.131` with appropriate SSH key