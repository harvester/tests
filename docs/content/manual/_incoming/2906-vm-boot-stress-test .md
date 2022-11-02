---
title: VM boot stress test 
---

* Related issues: [#2906](https://github.com/harvester/harvester/issues/2906) [BUG] VM can’t boot due to filesystem corruption

  
## Category: 
* Volume

## Verification Steps
1. Create volume (Harvester, Longhorn storage class)
1. Create volume from image
1. Unmount volume from VM
1. Delete volume in use and not in use
1. Export volume to image 
1. Create VM from the exported image
1. Edit volume to increase size 
1. Delete volume in use 
1. Clone volume 
1. Take volume snapshot
1. Restore volume snapshot 
1. Utilize the E2E test in harvester/test repo to prepare a script to continues run step 1-11 at lease 100 runs


## Expected Results
1. Pass more than 300 rounds of the I/O write test, should encounter data corruption issue and VM is alive
    ```
    opensuse:~ # xfs_info /dev/vda3
    meta-data=/dev/vda3              isize=512    agcount=13, agsize=653887 blks
            =                       sectsz=512   attr=2, projid32bit=1
            =                       crc=1        finobt=1, sparse=0, rmapbt=0
            =                       reflink=0
    data     =                       bsize=4096   blocks=7858427, imaxpct=25
            =                       sunit=0      swidth=0 blks
    naming   =version 2              bsize=4096   ascii-ci=0, ftype=1
    log      =internal log           bsize=4096   blocks=2560, version=2
            =                       sectsz=512   sunit=0 blks, lazy-count=1
    realtime =none                   extsz=4096   blocks=0, rtextents=0
    ```