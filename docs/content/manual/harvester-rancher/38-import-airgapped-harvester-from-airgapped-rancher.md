---
title: 38-Import Airgapped Harvester From the Airgapped Rancher
---

### Environment Setup

Setup the airgapped harvester
1. Fetch ipxe vagrant example with new offline feature
https://github.com/harvester/ipxe-examples/pull/32 
1. Edit the setting.xml file
1. Set offline: `true`
1. Use ipxe vagrant example to setup a 3 nodes cluster
1. Enable vlan on `bond0`
1. Now harvester dashboard page will out of work
1. We can't ssh to original assigned node ip
1. We need to ssh to 192.168.0.30, 31, 32 instead
1. Run `ip a | grep bond0` get the {ip-of-bond0}
1. Run the recover command
1. Confirm default route by using `ip r | grep default`
1. Wait for a while and access dashboard (it takes some time)
1. Create virtual machine with name `vlan1` and id: `1`
1. Open Settings, edit `http-proxy` with the following values
```
HTTP_PROXY=http://proxy-host:port
HTTPS_PROXY=http://proxy-host:port
NO_PROXY=localhost,127.0.0.1,0.0.0.0,10.0.0.0/8,192.168.0.0/16,cattle-system.svc,.svc,.cluster.local,<internal domain>
```

![image](https://user-images.githubusercontent.com/29251855/141812497-6664b1ae-42f9-4602-8e36-bd70f0b410c5.png)

1. Create ubuntu cloud image from URL
1. Create virtual machine and assign vlan network, confirm can get ip address

Setup squid HTTP proxy server
1. When you enabled `offline` in vagrant example, you don't need to install squid http proxy


Setup the airgapped harvester
1. Create an ubuntu virtual machine on localhost machine 
1. Assign `harvester` and `vagrant-libvirt` network to the virtual machine
1. Run `curl -fsSL https://get.docker.com | bash` to install docker
1. Pull rancher 2.6.2 image `docker pull rancher/rancher:2.6.2`
1. Query default route `ip r`
1. Remove default route `ip r delete {delte route}`
1. Run rancher container by command:
```
$ sudo docker run -d --restart=unless-stopped -p 80:80 -p 443:443 \
      -e HTTP_PROXY="http://192.168.0.1:3128" \
      -e HTTPS_PROXY="http://192.168.0.1:3128" \
      -e NO_PROXY="localhost,127.0.0.1,0.0.0.0,10.0.0.0/8,cattle-system.svc,192.168.0.0/24,.svc,.cluster.local,example.com" \
      --privileged rancher/rancher:v2.6.2
```
1. Login rancher and set access url 

### Test steps

1. Follow steps in `01-Import existing Harvester clusters in Rancher` to import harvester
1. Follow steps in `22-Create RKE2 Kubernetes Cluster` to provision RKE2 cluster


## Expected Results
1. Provision RKE2 cluster successfully with `Running` status
1. Can acccess RKE2 cluster to check all resources and services