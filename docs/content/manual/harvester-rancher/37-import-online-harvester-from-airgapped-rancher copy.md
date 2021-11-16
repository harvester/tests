---
title: 37-Import Online Harvester From the Airgapped Rancher
---

### Environment Setup

Setup the online harvester
1. Use ipxe vagrant example to setup a 3 nodes cluster
https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-harvester 
2. Enable vlan on `bond0`
3. Now harvester dashboard page will out of work
4. We can't ssh to original assigned node ip
5. We need to ssh to 192.168.0.30, 31, 32 instead
6. Run `ip a | grep bond0` get the {ip-of-bond0}
7. Run the recover command
8. Confirm default route by using `ip r | grep default`
9. Wait for a while and access dashboard (it takes some time)
10. Create ubuntu cloud image from URL
11. Create virtual machine with name `vlan1` and id: `1`
12. Create virtual machine and assign vlan network, confirm can get ip address

Setup squid HTTP proxy server
1. Move to vagrant pxe harvester folder
2. Execute `vagrant ssh pxe_server`
3. Run `apt-get install squid`
4. Edit `/etc/squid/squid.conf` and add line
```
http_access allow all
http_port 3128
```
5. Run `systemctl restart squid` 

Setup the airgapped harvester
1. Create an ubuntu virtual machine on localhost machine 
2. Assign `harvester` and `vagrant-libvirt` network to the virtual machine
3. Run `curl -fsSL https://get.docker.com | bash` to install docker
4. Pull rancher 2.6.2 image `docker pull rancher/rancher:2.6.2`
5. Query default route `ip r`
6. Remove default route `ip r delete {delte route}`
7. Run rancher container by command:
```
$ sudo docker run -d --restart=unless-stopped -p 80:80 -p 443:443 \
      -e HTTP_PROXY="http://192.168.0.1:3128" \
      -e HTTPS_PROXY="http://192.168.0.1:3128" \
      -e NO_PROXY="localhost,127.0.0.1,0.0.0.0,10.0.0.0/8,cattle-system.svc,192.168.0.0/24,.svc,.cluster.local,example.com" \
      --privileged rancher/rancher:v2.6.2
```
8. Login rancher and set access url 

### Test steps

1. Follow steps in `01-Import existing Harvester clusters in Rancher` to import harvester
2. Follow steps in `22-Create RKE2 Kubernetes Cluster` to provision RKE2 cluster


## Expected Results
1. Provision RKE2 cluster successfully with `Running` status
2. Can acccess RKE2 cluster to check all resources and services