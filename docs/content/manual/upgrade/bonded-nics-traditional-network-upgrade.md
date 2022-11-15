---
title: Upgrade Harvester with bonded NICs on network
---

* Related issues: [#3047](https://github.com/harvester/harvester/issues/3047) [BUG] migrate_harv_mgmt_to_mgmt_br.sh should remove ClusterNetwork resource


## Category: 
* Upgrade Harvester

## Environment setup from v1.0.3 upgrade to v1.1.1
1. Clone ipxe-example and switch to `v1.0` branch 
1. Add three additional Network interface in `Vagrantfile`
    ```
      harvester_node.vm.network 'private_network',
        libvirt__network_name: 'harvester',
        mac: @settings['harvester_network_config']['cluster'][node_number]['mac']
      harvester_node.vm.network 'private_network',
        libvirt__network_name: 'harvester'
      harvester_node.vm.network 'private_network',
        libvirt__network_name: 'harvester'
      harvester_node.vm.network 'private_network',
        libvirt__network_name: 'harvester'
    ```
1. Edit the config-create.yaml.j2 and config-join.yaml.j2 in /ansible/role/harvester/template/
1. Add the cluster_network and defaultPysicalNIC to `harvester-mgmt` 
    ```
    cluster_networks:
      vlan:
        enable: true
        description: "some description about this cluster network"
        config:
          defaultPhysicalNIC: harvester-mgmt
    
    ```
1. Bond multiple NICs on `harvester-mgmt` and `harvester-vlan` networks
    ```
    networks:
        harvester-mgmt:
          interfaces:
          - name: {{ settings['harvester_network_config']['cluster'][0]['mgmt_interface'] }}  # The management interface name
          - name: ens9
          method: dhcp
        bond0:
          interfaces:
          - name: {{ settings['harvester_network_config']['cluster'][0]['vagrant_interface'] }}
          method: dhcp
        harvester-vlan:
          interfaces:
          - name: ens7
          - name: ens8
          method: none
    
    ```

## Verification Steps
1. Provision previous version of Harvester cluster
1. For `VLAN 1` testing, enable network on settings, select `harvester-mgmt`
1. Create a `vlan1` network with id `1` on Networks page 
    ![image](https://user-images.githubusercontent.com/29251855/201606104-a1e23fd0-f04b-409e-818e-d1c514fea4e5.png)
1. For other VLAN id testing, enable network on settings, select correct network interface e.g `enps0f1`
    ![image](https://user-images.githubusercontent.com/29251855/201609582-d9e129f2-1c1e-416f-b878-9df4903ad2e2.png)
1. Create a `vlan91` network with available id `91` on Networks page (id number depends on your available network setting)
    ![image](https://user-images.githubusercontent.com/29251855/201609880-22bf619c-d215-403a-8299-63c62934cfe2.png)

1. Create images with different OS distribution
1. Create several virtual machines, set network to `management-network` or available `vlan` 
1. Create virtual machine on different target node
1. Setup NFS or S3 backup target in settings
1. Backup each virtual machines
1. Shutdown all virtual machines
1. Offline upgrade to target version, refer to https://docs.harvesterhci.io/v1.1/upgrade/automatic


## Expected Results
1. Can completely upgrade Harvester to specific version
1. Cluster Network exists
  ![image](https://user-images.githubusercontent.com/29251855/201101725-a028bc80-da8d-4708-8ecf-d3b5c7c66d0d.png)
1. Can create Vlan 1 on mgmt and route correctly
1. Can create other valid VLAN on specific NIC and route correctly
1. Check the network connectivity of vlan and management network
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

