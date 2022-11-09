---
title: VLAN Upgrade Test
---

* Related issues: [#2734](https://github.com/harvester/harvester/issues/2734) [FEATURE] VLAN enhancement upgrading
  
## Category: 
* Upgrade

## Verification Steps

### Test plan 1: harvester-mgmt vlan1
1. Prepare a 3 nodes `v1.0.3` Harvester cluster
1. Enable network on `harvester-mgmt`
1. Create vlan id `1`
1. Create two VMs, one set to vlan 1 and another use harvester-mgmt 
1. Perform manual upgrade to `v1.1.0`


### Test plan 2:  enps0 NIC with valid vlan
1. Prepare a 3 nodes `v1.0.3` Harvester cluster
1. Enable network on another NIC (eg. `enp129s0`)
1. Create vlan id `91` on `enp129s0`
1. Create two VMs, one set to vlan 91 and another use harvester-mgmt
1. Perform manual upgrade to `v1.1.0`

### Test plan 3: Bond mode using Harvester config file
1. Edit the ipxe-example add two additional NICs in Vagrantfile 
    ```
    harvester_node.vm.network 'private_network',
            libvirt__network_name: 'harvester'
        harvester_node.vm.network 'private_network',
            libvirt__network_name: 'harvester'
    ```
1. Add the `harvester-vlan` network in /ansible/roles/harvester/templates/config-create.yaml.j2
    ```
    install:
    mode: create
    networks:
        harvester-mgmt:
        interfaces:
        - name: {{ settings['harvester_network_config']['cluster'][0]['mgmt_interface'] }}  # The management interface name
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
1. Prepare a 1 nodes `v1.0.3` Harvester cluster using ipex-example 
1. Check the `harvester-vlan` link device status `ip -d l show dev harvester-vlan`
1. Create several vlan based on `harvester-vlan` interface
1. Create a VM with `vlan 1` network
1. The harvester-vlan config before upgrade
    ```
    harvester-vlan:
        interfaces:
        - name: ens7
            hwaddr: ""
        - name: ens8
            hwaddr: ""
        method: none
        ip: ""
        subnetmask: ""
        gateway: ""
        defaultroute: false
        bondoptions: {}
        mtu: 0
    ```


## Expected Results
1. Can successfully upgrade to v1.1.0
1. Check the network bridge `mgmt-br` exists `ip a`
1. Check there is `vlan 1` created on default cluster network (For Test plan1)
1. Check there is vlan with id created on related cluster network (For Test plan2)
1. Check the cluster networks contains `mgmt` and `vlan` (For Test plan3)
1. Check the yaml content of vlan1 (For Test plan1)
1. Check the yaml content of available vlan `91` (For Test plan2)
1. Check new network feature and UI work on v1.1.0
1. Check new network feature and UI, `vlan1` on `mgmt`, `vlan91` on `vlan` (For Test plan2)
