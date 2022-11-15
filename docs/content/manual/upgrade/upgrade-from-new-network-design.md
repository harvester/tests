---
title: Upgrade Harvester from new cluster network design (after v1.1.0)
---


## Category: 
* Upgrade Harvester

## Environment requirement
1. Network environment have available VLAN id setup on DHCP server can be assigned to Harvester
1. Network have at least two NICs
1. Suggest not to use SMR type HDD disk

We can select VM or Bare machine network setup according to available resource

## Virtual Machine environment setup
1. Clone ipxe-example https://github.com/harvester/ipxe-examples
1. Switch to main branch 
1. Edit Vagrantfile, add a new network interface of `pxe_server.vm.network` 
1. Set the `pxe_server.vm.network` bond to correct `libvirt` network
1. Add two additional new network interface of `harvester_node.vm.network`
1. Use ipxe-example to provision a multi nodes Harvester cluster
1. Run `varant ssh pxe_server` to access pxe server 
1. Edit the `dhcpd.conf`, let pxe server can create a vlan and assign IP to it 

## Bare machine environment setup
1. Ensure your switch router have setup available VLAN network
1. Setup the VLAN connectivity to your Router/Gateway device
1. Provision a multi nodes Harvester cluster


## Verification Steps
1. Open Cluster Networks/Configs
1. Create a new cluster network `vlan`
1. Create a network config under cluster network `vlan`
1. Select which node to use this config
1. Select NICs on the uplink page 
1. Open Networks page
1. Create vlan `1` network on `mgmt` cluster network
1. Create another vlan network on `vlan` cluster network in step 3
    ![image](https://user-images.githubusercontent.com/29251855/201615070-969e6c34-1a8e-4540-a750-32f7f38b585c.png)
1. Create images with different OS distribution
1. Create several virtual machines, set network to `management-network` or available `vlan` 
1. Create virtual machine on different target node
1. Setup NFS or S3 backup target in settings
1. Back each virtual machines
1. Shutdow all virtual machines
1. Offline upgrade to traget version, refer to https://docs.harvesterhci.io/v1.1/upgrade/automatic
1. Import Harvester into the Rancher cluster
1. Adding node after the upgrade


## Expected Results
1. Can completely upgrade Harvester to specific version
1. All pods is running correctly
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
1. Check the network connectivity of VLAN
1. Can restore VM from backup 
1. Can import Harvester in Rancher
1. Can add additional nodes to existing Harvester cluster
1. Can create new vms


