---
title: Attach unpartitioned NVMe disks to host
---

* Related issues: [#1414](https://github.com/harvester/harvester/issues/1414) Adding unpartitioned NVMe disks fails

## Category: 
* Storage

## Verification Steps
1. Use `qemu-img create -f qcow2` command to create three disk image locally
1. Shutdown target node VM machine
1. Directly edit VM xml content in virt manager page
1. Add <domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'> to the first line
1. Add the following line before the end of <domain> quote
```
<qemu:commandline>
    <qemu:arg value="-drive"/>
    <qemu:arg value="file=/home/davidtclin/Documents/Software/qemu_kvm/node_3/nvme301.img,if=none,id=D22"/>
    <qemu:arg value="-device"/>
    <qemu:arg value="nvme,drive=D22,serial=1234"/>
    <qemu:arg value="-drive"/>
    <qemu:arg value="file=/home/davidtclin/Documents/Software/qemu_kvm/node_3/nvme302.img,if=none,id=D23"/>
    <qemu:arg value="-device"/>
    <qemu:arg value="nvme,drive=D23,serial=1235"/>
    <qemu:arg value="-drive"/>
    <qemu:arg value="file=/home/davidtclin/Documents/Software/qemu_kvm/node_3/nvme303.img,if=none,id=D24"/>
    <qemu:arg value="-device"/>
    <qemu:arg value="nvme,drive=D24,serial=1236"/>
  </qemu:commandline>
```
1. Start VM node
1. Open Host page and edit the host config
1. Click Disk -> Add disk to select available nvme disks
1. Check disk can be mounted with `schedulable` and `running status` in edit node disk page

## Expected Results


