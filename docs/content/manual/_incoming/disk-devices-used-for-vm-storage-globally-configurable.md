---
title: Disk devices used for VM storage should be globally configurable
---

 * Related issue: [#1241](https://github.com/harvester/harvester/issues/1241) Disk devices used for VM storage should be globally configurable

 * Related issue: [#1382](https://github.com/harvester/harvester/issues/1382) Exclude OS root disk and partitions on forced GPT partition

 * Related issue: [#1599](https://github.com/harvester/harvester/issues/1599) Extra disk auto provision from installation may cause NDM can't find a valid longhorn node to provision

## Category: 
* Storage

## Test Scenarios
(Checked means verification `PASS`)
1. `BIOS` firmware + `No MBR` (Default) + Auto disk` provisioning config  
1. `BIOS` firmware + `MBR` + Auto disk provisioning config
1. `UEFI` firmware + `GPT` (Default) +  Auto disk provisioning config
1. `BIOS` firmware + `GPT` (Default) +Auto Provisioning on harvester-config


## Environment setup
* **Scenario 1**: 
  Node type: `Create`
  |Firmware|Harvester install|Auto provision|
  |-----|--------|--------|
  |BIOS|No MBR|set|

  Node type: `Join`
  |Firmware|Harvester Install|Auto provision|
  |-----|--------|--------|
  |BIOS|No MBR|No set|
   
* **Scenario 2**: 
  Node type: `Create`
  |Firmware|Harvester install|Auto provision|
  |-----|--------|--------|
  |BIOS|MBR|set|

  Node type: `Join`
  |Firmware|Harvester Install|Auto provision|
  |-----|--------|--------|
  |BIOS|MBR|No set|

* **Scenario 3**: 
  Node type: `Create`
  |Firmware|Harvester install|Auto provision|
  |-----|--------|--------|
  |UEFI|GPT|set|

  Node type: `Join`
  |Firmware|Harvester Install|Auto provision|
  |-----|--------|--------|
  |UEFI|GPT|No set|

### Storage Setup on VM

  - 150GB IDE storage (IDE: /dev/sdb) -> Harvester
  - 60GB SATA storage (SATA: /dev/sda)
  - 30 GB SCSI storage  (SCSI: /dev/sdc) 

### Additional context
To simulate UEFI, please use `zypper install qemu-ovmf-x86_64` 
Then select `/usr/share/qemu/ovmf-x86_64-code.bin` firmware while creating VM
![image](https://user-images.githubusercontent.com/29251855/143432509-352ef2f3-ac42-4deb-b161-9e358011496c.png)

## Verification Steps
1. Prepare server and storage according to different scenario
1. ISO install harvester
1. Send `ctrl+alt+F2` key change to console 
1. Login with rancher/rancher
1. Run `lsblk` to check all available disks
1. Run `gdisk /dev/sda or /sdb`
1. Press `W` to create GPT table
![image](https://user-images.githubusercontent.com/29251855/143419997-1d55ddd7-d7a7-4e3d-b3a2-2b4b9a42239f.png)
1. Prepare a lightweight http server 
1. Create a harvester-config.yaml file add the following lines content 
  ```
  system_settings:
    auto-disk-provision-paths: /dev/sd*
  ```
1. Put harvester-config on http server 
1. Send `ctrl+alt+F1` key back to iso installation
1. Input harvester config url (e.g http://192.168.1.106:8080/harvester-config.yaml) 
1. Wait for harvester installation complete
1. Access harvester and open Host page
1. Check all /dev/sda , /dev/sdb and /dev/sdc are provisioned and mounted correctly 

1. Prepare a BIOS virtual machine
1. Prepare extra disk 
1. ISO install harvester
1. Send `ctrl+alt+F2` key change to console 
1. Run `lsblk` to check all available disks
1. Run `gdisk /dev/sda or /sdb`
1. Press `W` to create GPT table
1. Prepare a lightweight http server 
1. Create a harvester-config.yaml file add the following lines content 
  ```
  system_settings:
    auto-disk-provision-paths: /dev/sd*
  ```
1. Put harvester-config on http server 
1. Send `ctrl+alt+F1` key back to iso installation
1. Input harvester config url (e.g http://192.168.1.106:8080/harvester-config.yaml) 
1. Wait for harvester installation complete
1. Access harvester and open Host page
1. Check all /dev/sda , /dev/sdb and /dev/sdc are provisioned and mounted correctly 


## Expected Results
For each of the three test scenarios need to bypass the following criteria

1. `BIOS` firmware + `No MBR` (Default) 
1. `BIOS` firmware + `MBR` 
1. `UEFI` firmware + `GPT` (Default) 
 
* Additional /dev/sda and /dev/sdc can be provision and scheduled correctly
* Harvester disk /dev/sdb can be provisioned correctly
* All disk auto provisioned correctly on second `join` node


1. The BIOS boot partition can be excluded from harvester installation.
1. And can complete `BIOS+GPT(Default)+Auto Provisioning` correctly with all disk partition provisioned and mounted

* GPT boot partition exclude and don't have label 
```
rancher@harvester-create-i1241:~> lsblk
'NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
loop0    7:0    0  3.2G  1 loop /
sda      8:0    0   50G  0 disk 
└─sda1   8:1    0   50G  0 part /var/lib/harvester/extra-disks/1aa2e715a2945bc942098183597ccd7b
sdb      8:16   0  150G  0 disk 
├─sdb1   8:17   0  960K  0 part 
├─sdb2   8:18   0   50M  0 part /oem
├─sdb3   8:19   0   15G  0 part /run/initramfs/cos-state
├─sdb4   8:20   0    8G  0 part 
├─sdb5   8:21   0   50G  0 part /usr/local
└─sdb6   8:22   0   77G  0 part /var/lib/longhorn
sdc      8:32   0   30G  0 disk 
└─sdc1   8:33   0   30G  0 part /var/lib/harvester/extra-disks/c079ea8222361d08b8d5bd8ce0038d0c
sdd      8:48   0   10M  0 disk /var/lib/kubelet/pods/1f9eea94-f19d-45ce-85f6-25cb6aba5518/volumes/kubernetes.io~csi/pvc-4063c5c7-28f5-4c74-8b26-ef17ed531c85/mount
sde      8:64   0   50G  0 disk /var/lib/kubelet/pods/9690de6e-2093-43f0-9ef3-170a96ffa8b3/volume-subpaths/pvc-b22ce226-2d61-460d-afd4-bcf98bf743d3/prometheus/2
sr0     11:0    1 1024M  0 rom
```

* No harvester disk (`/dev/sdb`) exists in blockdevice
```
harvester-create-i1241:/home/rancher # kubectl -n longhorn-system get blockdevices
NAME                               TYPE   DEVPATH     MOUNTPOINT                                                        NODENAME                 STATUS   AGE
112a2ebeaaa79dea6766b61003143a24   part   /dev/sda1   /var/lib/harvester/extra-disks/1aa2e715a2945bc942098183597ccd7b   harvester-create-i1241   Active   46m
297d8caa753e938463630856b464f5e0   part   /dev/sdc1   /var/lib/harvester/extra-disks/c079ea8222361d08b8d5bd8ce0038d0c   harvester-create-i1241   Active   46m
2ec6b9241bbfb96a57e6ea93b71b8806   part   /dev/sdc1   /var/lib/harvester/extra-disks/2bf5824103011662c7c505aa26dc372b   harvester-join-i1241     Active   27m
32f8bd586e02674773e06e5aea17003b   disk   /dev/sdc                                                                      harvester-create-i1241   Active   46m
5d4b21d5e1c49cae560aef651c395bbb   disk   /dev/sdc                                                                      harvester-join-i1241     Active   27m
7e23aa7c4e182fb234ae1f52742fea31   part   /dev/sda1   /var/lib/harvester/extra-disks/68486771d7f3bfc9041389e7c6b54409   harvester-join-i1241     Active   27m
b57f984a8c07bb8841516b494b2b7948   disk   /dev/sda                                                                      harvester-create-i1241   Active   46m
ef9867b432fedb4e619962865f521c94   disk   /dev/sda
```