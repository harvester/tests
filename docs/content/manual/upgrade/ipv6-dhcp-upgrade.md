---
title: Upgrade Harvester with IPv6 DHCP 
---

* Related issues: [#2962](https://github.com/harvester/harvester/issues/2962) [BUG] Host IP is inconsistent


## Category: 
* Upgrade Harvester

## Environment setup
1. Open the virtual machine manager 
1. Open the Connection Details -> Virtual Networks
1. Create a new virtual network `workload`
1. Add the following XML content 
    ```
    <network>
    <name>workload</name>
    <uuid>ac62e6bf-6869-41a9-a2b7-25c06c7601c9</uuid>
    <forward mode="nat">
        <nat>
        <port start="1024" end="65535"/>
        </nat>
    </forward>
    <bridge name="virbr5" stp="on" delay="0"/>
    <mac address="52:54:00:7b:ed:99"/>
    <domain name="workload"/>
    <ip address="192.168.101.1" netmask="255.255.255.0">
        <dhcp>
        <range start="192.168.101.128" end="192.168.101.254"/>
        </dhcp>
    </ip>
    <ip family="ipv6" address="fd7d:844d:3e17:f3ae::1" prefix="64">
        <dhcp>
        <range start="fd7d:844d:3e17:f3ae::100" end="fd7d:844d:3e17:f3ae::1ff"/>
        </dhcp>
    </ip>
    </network>
    ```
    
1. Change the bridge name to a new one 

    ![image](https://user-images.githubusercontent.com/29251855/201565649-ba54d6f7-3540-4a4b-ad66-ee4a77cfbff1.png)


## Verification Steps
1. Create a VM and use the customized ipv6 virtual network. (workload)
1. Doing an Harvester v1.0.3 ISO install with `create` new mode
1. Select DHCP node ip and DHCP vip during the installation 
1. Create another VMs use the customized ipv6 virtual network
1. Doing an Harvester v1.0.3 ISO install with `join` mode
1. Select DHCP node ip and DHCP vip during the installation
1. Offline upgrade to master release, refer to https://docs.harvesterhci.io/v1.1/upgrade/automatic
1. Check host IP on Host page 
1. Check the ip allocated to node `kubectl get nodes -o json | jq '.items[].status.addresses'` 


## Expected Results
1. Can completely upgrade from v1.0.3 to v1.1.0
1. The Host IP should not display IPv6 information and no `Host IP is inconsistent` error
  ![image](https://user-images.githubusercontent.com/29251855/201028253-5dee39dd-67d4-41c0-a38d-09ac397f3983.png)
  
1. Access node machine, check the IP information
    ```
    harv103-master:~ # kubectl get nodes -o json | jq '.items[].status.addresses'
    [
      {
        "address": "192.168.101.162",
        "type": "InternalIP"
      },
      {
        "address": "harv103-master",
        "type": "Hostname"
      }
    ]
    
    ```
1. Check the network connectivity of vlan and management network
1. Can completely upgrade Harvester to specific version
1. All pods are running correctly
1. Check can display Monitoring Chart 
   - Prometheus dashboard
   - VM metrics
1. Can access dashboard by VIP
1. Can use original password to login
1. Can start VM in running status
1. Image exists without corrupted
1. Volume exists
1. Virtual network exists
1. Backup exists
1. Setting value exists
1. Can restore VM from backup
1. Can create new VMs

