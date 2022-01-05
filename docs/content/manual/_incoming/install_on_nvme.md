---
title: Install Harvester on NVMe SSD
---
Ref: https://github.com/harvester/harvester/issues/1627

## Verify Items
  - Harvester can detect NVMe SSD when installing
  - Harvester can be installed on NVMe SSD

## Case: Install Harvester on NVMe disk
1. Create block image as NVMe disk
    - Run `dd if=/dev/zero of=/var/lib/libvirt/images/nvme145.img bs=1M count=148480`
    - Then Change file owner `chown qemu:qemu /var/lib/libvirt/images/nvme145.img`
2. Create VM via _virt-manager_
    - Select _Manual install_, set **Generic OS**, `Memory:9216`, `CPUs:8`, Uncheck _**enable storage...**_ and check **customize configuration before install**
    - Select _Firmware_ to use **UEFI x86_64** (use `usr/share/qemu/ovmf-x86_64-code.bin` in SUSE Leap 15.3)
    - Select _Chipset_ to use **i440FX**
    - Click **Add Hardware** to add CD-ROM including Harvester iso
    - Update **Boot Options** to **Enable boot menu** and enable the CD-ROM
    - edit XML with update `<domain type="kvm">` to `<domain type="kvm" xmlns:qemu="http://libvirt.org/schemas/domain/qemu/1.0">`
    - append NVMe xml node into **domain**, then Begin Installation
```xml
  <qemu:commandline>
    <qemu:arg value="-drive"/>
    <qemu:arg value="file=/var/lib/libvirt/images/nvme.img,if=none,id=D22,format=raw"/>
    <qemu:arg value="-device"/>
    <qemu:arg value="nvme,drive=D22,serial=1234"/>
  </qemu:commandline>
```
3. Install Harvester by the console UI
4. When rebooting, _**Press ESC**_ to enter UEFI
![image](https://user-images.githubusercontent.com/5169694/146147904-26c50129-020b-4e52-ac1a-95a6814edde7.png)
    - If you miss the screen, VM will entering the Grub with **Harvester Installer** option, you have to reboot again
5. Select **Boot Manager**
![image](https://user-images.githubusercontent.com/5169694/146148422-eab0f144-3b52-455a-b372-e2237001e567.png)
6. Select **UEFI QEMU NVME Ctrl ...**
![image](https://user-images.githubusercontent.com/5169694/146148533-aeb502c3-52f8-4f1b-bc2a-b213ed4fee03.png)
7. VM should boot into Harvester successfully