---
title: Disk can only be added once on UI
---
Ref: https://github.com/harvester/harvester/issues/1608

## Verify Items
  - NVMe disk can only be added once on UI

## Case: add new NVMe disk on dashboard UI
1. Install Harvester with 2 nodes
1. Power off 2nd node
1. Update VM's xml definition (by using `virsh edit` or virt-manager)
    - Create **nvme.img** block: `dd if=/dev/zero of=/var/lib/libvirt/images/nvme.img bs=1M count=4096`
    - change owner `chown qemu:qemu /var/lib/libvirt/images/nvme.img`
    - update `<domain type="kvm">` to `<domain type="kvm" xmlns:qemu="http://libvirt.org/schemas/domain/qemu/1.0">`
    - append xml node into **domain** as below:
```xml
  <qemu:commandline>
    <qemu:arg value="-drive"/>
    <qemu:arg value="file=/var/lib/libvirt/images/nvme.img,if=none,id=D22,format=raw"/>
    <qemu:arg value="-device"/>
    <qemu:arg value="nvme,drive=D22,serial=1234"/>
  </qemu:commandline>
```
1. Power on 2nd node
1. login to dashboard, then click `Edit Config` on 2nd node
1. Navigate to **Disks** tab, then add the NVMe disk from the drop-down list of **Add Disk**
1. The NVMe disk should disappear from the drop-down list
1. Cick **Save**, `Edit Config` on 2nd node again
1. The NVMe disk should not able to be added again
![image](https://user-images.githubusercontent.com/5169694/145861027-2b7575c8-a467-43eb-99ca-28a7c0026dba.png)
![image](https://user-images.githubusercontent.com/5169694/145861276-d9cab21a-7c82-4287-af2f-3b60fab11a3f.png)
