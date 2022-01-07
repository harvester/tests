---
title: Manual upgrade from 0.3.0 to 1.0.0
---

* Related issues: [#1644](https://github.com/harvester/harvester/issues/1644) Harvester pod crashes after upgrading from v0.3.0 to v1.0.0-rc1 (contain vm backup before upgrade) 

* Related issues: [#1588](https://github.com/harvester/harvester/issues/1588) VM backup cause harvester pod to crash 

## Notice
We recommend using zero downtime upgrade to upgrade harvester.
Manual upgrade is for advance usage and purpose.

## Category: 
* Manual Upgrade

## Verification Steps
1. Download harvester v0.3.0 iso and do checksum
1. Download harvester v1.0.0 iso and do checksum
1. Use ISO Install a 4 nodes harvester cluster 
1. Create several OS images from URL
1. Create ssh key
1. Enable vlan network with `harvester-mgmt`
1. Create virtual network `vlan1` with id `1`
1. Create 2 virtual machines
  - ubuntu-vm: 2 core, 4GB memory, 30GB disk
1. Setup backup target
1. Take a backup from ubuntu vm
1. Peform manual upgrade steps in the following docudment

**upgrade process**
Follow the manual upgrade steps to upgrade from v0.3.0 to v1.0.0-rc1
https://github.com/harvester/docs/blob/a4be9a58441eeee3b5564b70e499dc69c6040cc8/docs/upgrade.md 


## Expected Results
1. Check Harvester pods should not crash 
```
harvester-node01-upgrade100rc1:/home/rancher # kubectl get pods -n harvester-system
NAME                                                     READY   STATUS      RESTARTS   AGE
harvester-d544ddb6f-52mdk                                1/1     Running     0          58m
harvester-d544ddb6f-mg4dc                                1/1     Running     0          58m
harvester-d544ddb6f-npd7c                                1/1     Running     0          58m
harvester-load-balancer-59bf75f489-57nnp                 1/1     Running     0          58m
harvester-network-controller-68m6r                       1/1     Running     0          57m
harvester-network-controller-cdrjp                       1/1     Running     0          57m
harvester-network-controller-jfg96                       1/1     Running     0          58m
harvester-network-controller-manager-c57f8cbcb-67mcq     1/1     Running     0          58m
harvester-network-controller-manager-c57f8cbcb-9mqbx     1/1     Running     0          58m
harvester-network-controller-v2k2n                       1/1     Running     0          57m
harvester-node-disk-manager-29xrr                        1/1     Running     0          57m
harvester-node-disk-manager-v27hz                        1/1     Running     0          57m
harvester-node-disk-manager-wwpwf                        1/1     Running     0          58m
harvester-node-disk-manager-zwbxv                        1/1     Running     0          57m
harvester-promote-harvester-node02-upgrade100rc1-nphjz   0/1     Completed   0          9h
harvester-promote-harvester-node03-upgrade100rc1-72lj7   0/1     Completed   0          9h
harvester-webhook-67744f845f-pmrlg                       1/1     Running     0          57m
harvester-webhook-67744f845f-r5c44                       1/1     Running     0          58m
harvester-webhook-67744f845f-tqjkl                       1/1     Running     0          57m
kube-vip-2l2qp                                           1/1     Running     1          56m
kube-vip-cloud-provider-0                                1/1     Running     34         10h
kube-vip-cvklf                                           1/1     Running     0          56m
kube-vip-q99lt                                           1/1     Running     0          56m
virt-api-86455cdb7d-2hb4x                                1/1     Running     3          10h
virt-api-86455cdb7d-q8fpc                                1/1     Running     3          10h
virt-controller-5f649999dd-q5bqs                         1/1     Running     18         10h
virt-controller-5f649999dd-sqh9g                         1/1     Running     20         10h
virt-handler-4ncxn                                       1/1     Running     3          10h
virt-handler-cmzg2                                       1/1     Running     3          9h
virt-handler-k8pg9                                       1/1     Running     3          10h
virt-handler-x754t                                       1/1     Running     2          8h
virt-operator-56c5bdc7b8-cgwc8                           1/1     Running     28         10h
```

1. Check whether longhornBackupName is in each VM Backup.

    ```
    $ kubectl get backup -A
    longhorn-system   backup-7933c0d09ec04d1a   snapshot-b1fbfcf4-ad45-442d-9bb6-8119e713d892   1367343104     2021-12-17T07:13:00Z   Completed   2021-12-17T07:17:51.097572079Z

    ```

    ```
    $ kubectl get vmbackup ubuntu-backup -o yaml | less

    volumeBackups:
    - creationTime: "2021-12-17T07:12:59Z"
        longhornBackupName: backup-7933c0d09ec04d1a
        name: ubuntu-backup-volume-ubuntu-vm-disk-0-ylodf
    ```

1. Check whether there is <namespace>-<name>.cfg file in backup target.
  There is a default-ubuntu-backup.cfg file exists on S3 backup remote bucket 

    ``` $ cat default-ubuntu-backup.cfg ```

    ![image](https://user-images.githubusercontent.com/29251855/146564069-24d2f5d0-5b98-438d-b909-cf53ad2691ce.png)

1. Check whether you can restore VM.
    Can create a new vm from restore the existing backup  

    ```
    ![image](https://user-images.githubusercontent.com/29251855/146564664-46809072-a320-44a6-8665-29aa1b8d936f.png)


    ```

