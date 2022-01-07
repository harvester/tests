---
title: Automatically get VIP during PXE installation
---

* Related issues: [#1410](https://github.com/harvester/harvester/issues/1410) Support getting VIP automatically during PXE boot installation

## Verification Steps

1. Comment `vip` and `vip_hw_addr` in `ipxe-examples/vagrant-pxe-harvester/ansible/roles/harvester/templates/config-create.yaml.j2`
1. Start vagrant-pxe-harvester
1. Run `kubectl get cm -n harvester-system vip`
    - Check whether we can get `ip` and `hwAddress` in it
1. Run `ip a show harvester-mgmt`
    - Check whether there are two IPs in it and one is the vip.

## Expected Results
1. VIP should automatically be assigned