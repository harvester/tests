---
title: Move Longhorn storage to another partition
---

 * Related issue: [#1316](https://github.com/harvester/harvester/issues/1316) Move Longhorn storage to another partition

## Category: 
* Storage

## Test Scenarios
![image](https://user-images.githubusercontent.com/29251855/148171176-5dfe439b-8f61-484b-8c16-9c0236a5c1f2.png)

* Case 1: UEFI + GPT (Disk < MBR Limit) 
* Case 2: BIOS + No MBR (Disk < MBR Limit) 
* Case 3: BIOS + Force MBR (Disk < MBR Limit) 
* Case 4: BIOS + No MBR (Disk > MBR Limit)
* Case 5: BIOS + Force MBR (Disk > MBR Limit)
* Case 6: UEFI + GPT (Disk > MBR Limit)



## Environment setup
* Test Environment: 1 node harvester on local kvm machine

* Disk usage information:
  - Disk < MBR Limit: 150GB IDE
  - Disk > MBR Limit: 2.5TB SATA

## Verification Steps
1. Create a virtual machine
1. Set virtual machine with different BIOS system
1. Add disk more or less than MBR limit (2.5TiB)
1. For Disk > MBR Limit test scenario -> add a 2.5TiB SATA disk 
1. Iso install harvester
1. For Disk > MBR Limit test scenario -> set SATA disk as the 1st boot priority 
1. Check can finish installation 
1. Check disk information in host page
1. SSH to server node, run `lsblk` check disk information

## Expected Results
1. Case1: UEFI + GPT (Disk < MBR Limit) 

* Installation complete
* partition is mounted to /var/lib/longhorn
```
rancher@harvester-uefi-gpt-lmax-i1316-1201:~> lsblk
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
loop0    7:0    0  3.2G  1 loop /
sda      8:0    0  150G  0 disk 
├─sda1   8:1    0   47M  0 part 
├─sda2   8:2    0   50M  0 part /oem
├─sda3   8:3    0   15G  0 part /run/initramfs/cos-state
├─sda4   8:4    0    8G  0 part 
├─sda5   8:5    0   50G  0 part /usr/local
└─sda6   8:6    0 76.9G  0 part /var/lib/longhorn
sdb      8:16   0   10M  0 disk /var/lib/kubelet/pods/e55ecade-ea18-4f4d-9cbd-933e935195a6/volumes/kubernetes.io~csi/pvc-a5b69249-d288-41d3-8cec-63d34d0691d1/mount
sdc      8:32   0   50G  0 disk /var/lib/kubelet/pods/ab573a07-fab1-4889-b1ce-8fddc9eec2c3/volume-subpaths/pvc-11b9e17a-2d29-49dc-ba0e-47758f30bd7f/prometheus/2
sr0     11:0    1 1024M  0 rom
```

1. Case2: BIOS + No MBR (Disk < MBR Limit) `PASS`
* Installation complete
* partition is mounted to /var/lib/longhorn
```
rancher@harvester-bios-gpt-lmax-i1316-1201:~> lsblk
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
loop0    7:0    0  3.2G  1 loop /
sda      8:0    0  200G  0 disk 
├─sda1   8:1    0  960K  0 part 
├─sda2   8:2    0   50M  0 part /oem
├─sda3   8:3    0   15G  0 part /run/initramfs/cos-state
├─sda4   8:4    0    8G  0 part 
├─sda5   8:5    0   60G  0 part /usr/local
└─sda6   8:6    0  117G  0 part /var/lib/longhorn
sdb      8:16   0   10M  0 disk /var/lib/kubelet/pods/a67f9918-db84-4267-a8ae-670e17b6baa1/volumes/kubernetes.io~csi/pvc-f909384f-0374-4611-b577-c0fa8caa77fb/mount
sdc      8:32   0   50G  0 disk /var/lib/kubelet/pods/ebe71b81-750d-4481-8022-ffb4f61ab3f3/volume-subpaths/pvc-d511c684-e8cb-4308-a1e6-1c84a0cc6f76/prometheus/2
sr0     11:0    1 1024M  0 rom
```
3. Case 3: BIOS + Force MBR (Disk < MBR Limit) `PASS`
* Installation complete
*  run lsblk and verify there are only 4 partitions:
```
rancher@harvester-bios-mbr-lmax-i1316-1201:~> lsblk
NAME   MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
loop0    7:0    0   3.2G  1 loop /
sda      8:0    0   150G  0 disk 
├─sda1   8:1    0    47M  0 part /oem
├─sda2   8:2    0    14G  0 part /run/initramfs/cos-state
├─sda3   8:3    0   7.5G  0 part 
└─sda4   8:4    0 128.5G  0 part /usr/local
sdb      8:16   0    10M  0 disk /var/lib/kubelet/pods/c9fbcc54-e6e1-4085-a5fb-cf4bc7f1088b/volumes/kubernetes.io~csi/pvc-01622ebc-427a-4e86-aed5-baf7ed2752b7/mount
sdc      8:32   0    50G  0 disk /var/lib/kubelet/pods/93d20407-36ad-437c-8928-c8dfb0b07983/volume-subpaths/pvc-dbb9dcc1-bd7b-4ca1-8836-1e2d736fa3ec/prometheus/2
sr0     11:0    1  1024M  0 rom
```
* Device `/dev/sda` has MBR partitioning scheme
```
harvester-bios-mbr-lmax-i1316-1201:/home/rancher # gdisk /dev/sda
GPT fdisk (gdisk) version 1.0.1

Partition table scan:
  MBR: MBR only
  BSD: not present
  APM: not present
  GPT: not present


***************************************************************
Found invalid GPT and valid MBR; converting MBR to GPT format
in memory. THIS OPERATION IS POTENTIALLY DESTRUCTIVE! Exit by
typing 'q' if you don't want to convert your MBR partitions
to GPT format!
***************************************************************


Warning! Secondary partition table overlaps the last partition by
33 blocks!
You will need to delete this partition or resize it in another utility.
```

4. Case 4: BIOS + No MBR (Disk > MBR Limit) `PASS`

![image](https://user-images.githubusercontent.com/29251855/144211328-7c264dfd-5a7a-4c89-90c6-85584a7634b1.png)

* Installation complete
![image](https://user-images.githubusercontent.com/29251855/144220543-07f9b940-7ed6-462d-a09b-a6029cfcc473.png)
* Partition is created and is mounted to /var/lib/longhorn:
```
rancher@harvester-bios-gpt-gmax-i1316-1201:~> lsblk
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
loop0    7:0    0  3.2G  1 loop /
sda      8:0    0  150G  0 disk 
sdb      8:16   0  2.4T  0 disk 
├─sdb1   8:17   0  960K  0 part 
├─sdb2   8:18   0   50M  0 part /oem
├─sdb3   8:19   0   15G  0 part /run/initramfs/cos-state
├─sdb4   8:20   0    8G  0 part 
├─sdb5   8:21   0  100G  0 part /usr/local
└─sdb6   8:22   0  2.3T  0 part /var/lib/longhorn
sdc      8:32   0   10M  0 disk /var/lib/kubelet/pods/322cb1fb-9e2c-4bb2-ad7e-c2ab27581ff3/volumes/kubernetes.io~csi/pvc-6fc0ecd3-0162-410e-ab93-49ade79f37b2/mount
sdd      8:48   0   50G  0 disk /var/lib/kubelet/pods/e140a2a2-626a-495e-9f8e-47912a241048/volume-subpaths/pvc-9bf51cd2-1fb7-464e-af45-3ecc21f654fa/prometheus/2
sr0     11:0    1 1024M  0 rom
```

5. Case 5: BIOS + Force MBR (Disk > MBR Limit) -> `PASS`
ISO installer will prompt message and prevent user to proceed if select disk size > MBR Limit
`Disk too large for MBR. Must be less than 2TiB`
![image](https://user-images.githubusercontent.com/29251855/144215424-8333b909-63b7-4383-bae6-ab6418d21cce.png)


6. Case 6: UEFI + GPT (Disk > MBR Limit) `PASS` 

![image](https://user-images.githubusercontent.com/29251855/144224629-9ba66eea-80ad-4070-9d3d-b3b5ca310758.png)

* Installation complete 
![image](https://user-images.githubusercontent.com/29251855/144227436-a7d925d9-94cd-434b-ba75-5c3532e5b6a3.png)


* partition is mounted to /var/lib/longhorn
```
rancher@harvester-uefi-gpt-gmax-i1316-1201:~> lsblk
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
loop0    7:0    0  3.2G  1 loop /
sda      8:0    0  2.4T  0 disk 
├─sda1   8:1    0   47M  0 part 
├─sda2   8:2    0   50M  0 part /oem
├─sda3   8:3    0   15G  0 part /run/initramfs/cos-state
├─sda4   8:4    0    8G  0 part 
├─sda5   8:5    0  100G  0 part /usr/local
└─sda6   8:6    0  2.3T  0 part /var/lib/longhorn
sdb      8:16   0   50G  0 disk /var/lib/kubelet/pods/42775ca9-faa0-443c-bfc0-1e3188014fbb/volume-subpaths/pvc-983a46d1-7378-4604-bccd-f4509c231d8b/prometheus/2
sdc      8:32   0   10M  0 disk /var/lib/kubelet/pods/6b59fd54-c546-4d1c-957c-1167c84674e5/volumes/kubernetes.io~csi/pvc-e57d512a-07f6-4f9e-bd8b-4febfd09482e/mount
```