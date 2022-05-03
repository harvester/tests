---
title: 57-Import airgapped harvester from airgapped rancher with Proxy
---

* Related task: [#1052](https://github.com/harvester/harvester/issues/1052) Test Air gap with Rancher integration


### Environment Setup

Setup the airgapped harvester
1. Fetch ipxe vagrant example with new offline feature
https://github.com/harvester/ipxe-examples/pull/32 
1. Edit the setting.xml file
1. Set offline: `true`
1. Use ipxe vagrant example to setup a 3 nodes cluster
1. Enable vlan on `harvester-mgmt`
1. Now harvester dashboard page will out of work
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
1. Pull latest rancher image `docker pull rancher/rancher:2.6.3-rc6`
1. Run rancher container by command:
```
$sudo docker run -d --restart=unless-stopped -p 80:80 -p 443:443 \
-e HTTP_PROXY="http://192.168.0.254:3128" \
-e HTTPS_PROXY="http://192.168.0.254:3128" \
-e NO_PROXY="localhost,127.0.0.1,0.0.0.0,10.0.0.0/8,cattle-system.svc,192.168.0.0/16,.svc,.cluster.local,example.com" \
--privileged rancher/rancher:v2.6.3-rc6
```
1. Login rancher and set access url
1. Set the following in Advanced - user data in the create RKE2 cluster page
  ```
  #cloud-config
  apt:
    http_proxy: http://192.168.0.254:3128
    https_proxy: http://192.168.0.254:3128
  ```
  ![image](https://user-images.githubusercontent.com/29251855/146680197-d78ef411-7ef8-42ce-b2b8-0036c7dc85c9.png)
1. In Cluster Configuration - Agent Environment Vars, add the following
  ```
  HTTP_PROXY: http://192.168.0.254:3128
  HTTPS_PROXY: http://192.168.0.254:3128
  NO_PROXY: localhost,127.0.0.1,0.0.0.0,10.0.0.0/8,cattle-system.svc,.svc,.cluster.local
  ```

  ![image](https://user-images.githubusercontent.com/29251855/146680338-922b0c6c-ebac-49c7-b4d5-dc68c534689b.png)

1. Create 4 core, 8GB RKE2 cluster in harvester   

### Test steps

1. Follow steps in `01-Import existing Harvester clusters in Rancher` to import harvester
1. Follow steps in `22-Create RKE2 Kubernetes Cluster` to provision RKE2 cluster


## Expected Results
1. Can import harvester from Rancher correctly 
1. Can access downstream harvester cluster from Rancher dashboard 
1. Can provision at least one node RKE2 cluster to harvester correctly with running status
1. Can explore provisioned RKE2 cluster nodes 
1. RKE2 cluster VM created running correctly on harvester node