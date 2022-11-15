---
title: Upgrade Harvester with HDD Disks
---


## Category: 
* Upgrade Harvester

## Environment requirement
1. Network environment have available VLAN id setup on DHCP server can be assigned to Harvester
1. Network have at least two NICs
1. Use HDD disk with SMR type or slow I/O speed
    ```
    n1-103:~ # smartctl -a /dev/sda
    smartctl 7.2 2021-09-14 r5237...
    === START OF INFORMATION SECTION ===
    Model Family:     Seagate BarraCuda 3.5 (SMR)
    ```

## Verification Steps
1. Create images with different OS distribution
1. Create several virtual machines, set network to `management-network` or available `vlan` 
1. Create virtual machine on different target node
1. Setup NFS or S3 backup target in settings
1. Backup each virtual machines
1. Shutdown all virtual machines
1. Offline upgrade to target version, refer to https://docs.harvesterhci.io/v1.1/upgrade/automatic
1. Apply the increase the job deadline workaround before clicking the upgrade button on dashboard
    ```
    $ cat > /tmp/fix.yaml <<EOF
    spec:
    values:
        systemUpgradeJobActiveDeadlineSeconds: "3600"
    EOF

    $ kubectl patch managedcharts.management.cattle.io local-managed-system-upgrade-controller --namespace fleet-local --patch-file=/tmp/fix.yaml --type merge
    $ kubectl -n cattle-system rollout restart deploy/system-upgrade-controller
    ```


## Expected Results
1. Can completely upgrade Harvester to specific version
1. All pods is running correctly
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
1. Check the network connectivity of VLAN
1. Can restore VM from backup 
1. Can import Harvester in Rancher
1. Can add additional nodes to existing Harvester cluster
1. Can create new vms


