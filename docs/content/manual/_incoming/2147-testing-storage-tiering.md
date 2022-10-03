---
title: Testing Harvester Storage Tiering
---

* Related issues: [#2147](https://github.com/harvester/harvester/issues/2147) [[FEATURE] Storage Tiering

## Category: 
* Images
* Volumes
* VirtualMachines

## Test Setup Steps
1. Have a Harvester Node with 3 Disks in total (one main disk, two additional disks), ideally the two additional disks should be roughly 20/30Gi for testing
1. Add the additional disks to the harvester node (you may first need to be on the node itself and do a `sudo gdisk /dev/sda` and then `w` and `y` to write the disk identifier so that Harvester can recogonize the disk, note you shouldn't need to build partitions)
1. Add the disks to the Harvester node via: Hosts -> Edit Config -> Storage -> "Add Disk" (call-to-action), they should auto populate with available disks that you can add 
1. Save
1. Navigate back to Hosts -> Host -> Edit Config -> Storage, then add a Host Tag, and a unique disk tag for every disk (including the main disk/default-disk) 


## Verification Steps with Checks
1. Navigate to Advanced -> Storage Classes -> Create (Call-To-Action), create a storageClass "sc-a", specify nodeSelector (choose host), diskSelector (choose one of the unique disk tags), number of replicas (1-12)
1. Also create a storageClass "sc-b", specify nodeSelector (choose host), diskSelector (choose one of the unique disk tags), number of replicas (1-12)
1. Create a new image img-a, specify storageClassName to sc-a
1. Create a new vm vm1 use the image img-a
1. Check the replicas number and location of rootdisk volume in longhorn UI
1. Create a new volume volume-a by choose source=image img-a
1. Add the volume volume-a to vm vm1
1. Check the replicas number and location of volume volume-a in longhorn UI:
    1. volume-a, should also be seen in `kubectl get pv --all-namespaces` (where "Claim" is volume-a) with the appropriate storage class
    1. also with something like `kubectl describe pv/pvc-your-uuid-from-get-pv-call-with-volume-a --all-namespaces`:
        1. can audit volume attributes like:
        ```
            VolumeAttributes:      diskSelector=second
                           migratable=true
                           nodeSelector=node-2
                           numberOfReplicas=1
                           share=true
                           staleReplicaTimeout=30
                           storage.kubernetes.io/csiProvisionerIdentity=1665780638152-8081-driver.longhorn.io
        ```  
        1. you can also notice the increase of % used & % allocated in longhorn underneath the node and disk like: `Path:  /var/lib/harvester/extra-disks/uuid-of-disk`
1. Export the image volume volume-a to a new image img-b and specify storageClassName sc-b
1. Create a new volume volume-b by choose source=image img-b
1. Add the volume volume-b to vm vm1
1. Check the replicas number and location of volume volume-b in longhorn UI:
    1. volume-b, should also be seen in `kubectl get pv --all-namespaces` (where "Claim" is volume-b) with the appropriate storage class
    1. also with something like `kubectl describe pv/pvc-your-uuid-from-get-pv-call-with-volume-b --all-namespaces`:
        1. can audit volume attributes like:
        ```
            VolumeAttributes:      diskSelector=second
                           migratable=true
                           nodeSelector=node-2
                           numberOfReplicas=1
                           share=true
                           staleReplicaTimeout=30
                           storage.kubernetes.io/csiProvisionerIdentity=1665780638152-8081-driver.longhorn.io
        ```
    1. you can also notice the increase of % used & % allocated in longhorn underneath the node and disk like: `Path:  /var/lib/harvester/extra-disks/uuid-of-disk`
1. Create a volume snapshot snapshot-a from volume-a
1. Create a new volume volume-c by choose Source=New and specify storageClassName sc-a
1. Add the volume volume-c to vm vm1
1. Check the replicas number and location of volume volume-c in longhorn UI:
    1. volume-c, should also be seen in `kubectl get pv --all-namespaces` (where "Claim" is volume-c) with the appropriate storage class
    1. also with something like `kubectl describe pv/pvc-your-uuid-from-get-pv-call-with-volume-c --all-namespaces`:
        1. can audit volume attributes like:
        ```
            VolumeAttributes:      diskSelector=second
                           migratable=true
                           nodeSelector=node-2
                           numberOfReplicas=1
                           share=true
                           staleReplicaTimeout=30
                           storage.kubernetes.io/csiProvisionerIdentity=1665780638152-8081-driver.longhorn.io
        ```   
    1. you can also notice the increase of % used & % allocated in longhorn underneath the node and disk like: `Path:  /var/lib/harvester/extra-disks/uuid-of-disk`
1. Create a volume snapshot snapshot-c from volume-c
1. Restore the volume snapshot snapshot-c to a new volume volume-restore-c and specify storageClassName sc-b, attach volume-restore-c to vm1
1. Check the replicas number and location of volume volume-restore-c in longhorn UI:
    1. volume-restore-c, should also be seen in `kubectl get pv --all-namespaces` (where "Claim" is volume-restore-c) with the appropriate storage class
    1. also with something like `kubectl describe pv/pvc-your-uuid-from-get-pv-call-with-volume-restore-c --all-namespaces`:
        1. can audit volume attributes like:
        ```
            VolumeAttributes:      diskSelector=second
                           migratable=true
                           nodeSelector=node-2
                           numberOfReplicas=1
                           share=true
                           staleReplicaTimeout=30
                           storage.kubernetes.io/csiProvisionerIdentity=1665780638152-8081-driver.longhorn.io
        ``` 
    1. you can also notice the increase of % used & % allocated in longhorn underneath the node and disk like: `Path:  /var/lib/harvester/extra-disks/uuid-of-disk`
1. Verify you should be able to edit the description of sc-a 
1. Verify that other elements should not be able to be edited for sc-a