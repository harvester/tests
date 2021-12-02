---
title: 54-Import Airgapped Harvester From the Online Rancher
---

### Environment Setup

Setup the airgapped harvester
1. Fetch ipxe vagrant example with new offline feature
https://github.com/harvester/ipxe-examples/pull/32 
1. Edit the setting.xml file
1. Set offline: `true`
1. Use ipxe vagrant example to setup a 3 nodes cluster
https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-harvester 
1. Enable vlan on `harvester-mgmt`
1. Now harvester dashboard page will out of work
1. Open Settings, edit `http-proxy` with the following values
```
HTTP_PROXY=http://proxy-host:port
HTTPS_PROXY=http://proxy-host:port
NO_PROXY=localhost,127.0.0.1,0.0.0.0,10.0.0.0/8,192.168.0.0/16,cattle-system.svc,.svc,.cluster.local,<internal domain>
```
1. Create ubuntu cloud image from URL
1. Create virtual machine with name `vlan1` and id: `1`
1. Create virtual machine and assign vlan network, confirm can get ip address

Setup squid HTTP proxy server
1. Move to vagrant pxe harvester folder
1. Execute `vagrant ssh pxe_server`
1. Run `apt-get install squid`
1. Edit `/etc/squid/squid.conf` and add line
```
http_access allow all
http_port 3128
```
1. Run `systemctl restart squid` 

Setup the online rancher
1. Create an ubuntu virtual machine on localhost machine 
1. Assign virtual network with internet connection to ubuntu host VM
1. Run `curl -fsSL https://get.docker.com | bash` to install docker
1. Run rancher container by command:
```
$ sudo docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:v2.6-head
```
1. Login rancher and set access url 

### Test steps

1. Access Rancher dashboard
1. Navigate to Virtualization Management page
1. Import existing harvester
1. copy the registration URL
1. Access Harvester
1. Input registration URL
1. Create cloud credential 
1. Provision a RKE1 cluster to harvester 
1. Provision a RKE1 cluster to harvester

## Expected Results
1. Can import harvester from Rancher correctly 
1. Can access downstream harvester cluster from Rancher dashboard 
1. Can provision at least one node RKE2 cluster to harvester correctly with running status
1. Can explore provisioned RKE2 cluster nodes 
1. RKE2 cluster VM created running correctly on harvester node