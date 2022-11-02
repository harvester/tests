---
title: Check version compatibility during an upgrade
---

* Related issues: [#2431](https://github.com/harvester/harvester/issues/2431) [FEATURE] Check version compatibility during an upgrade

  
## Category: 
* Upgrade

## Verification Steps

### Test Plan 1: v1.0.2 upgrade to v1.1.0 with release tag
### Test Plan 2: v1.0.3 upgrade to v1.1.0 with release tag
### Test Plan 3: v1.0.2 upgrade to v1.1.0 without release tag

1. Prepare v1.0.2, v1.0.3 Harvester ISO image
1. Prepare v1.1.0 ISO image with release tag
1. Prepare v1.1.0 ISO image without release tag
1. Put different ISO image to HTTP server 
1. Create the upgrade yaml to create service 
    ```
    cat <<EOF | kubectl apply -f -
    apiVersion: harvesterhci.io/v1beta1
    kind: Version
    metadata:
        name: v1.1.0
        namespace: harvester-system
    spec:
        isoURL: "http://192.168.1.110:8000/harvester-eeeb1be-dirty-amd64.iso"
    EOF
    ```
1. Upgrade from v1.0.2 upgrade to v1.1.0 with release tag
1. Upgrade from v1.0.3 to v1.1.0 with release tag
1. Upgrade from v1.0.2 to v1.1.0 without release tag 

## Expected Results

### Test Result 1
1. Upgrade from v1.0.2 upgrade to v1.1.0 with release tag `failed` on upgrade dashboard UI
    ![image](https://user-images.githubusercontent.com/29251855/193567678-7653aa7b-b93a-4cf2-98a8-37e4fcfd06f6.png)

1. The upgrade pod display `Error` 
    ```
    harvester102:/home/rancher # kubectl -n harvester-system get po -l harvesterhci.io/upgradeComponent=manifest
    NAME                                       READY   STATUS   RESTARTS   AGE
    hvst-upgrade-xtkwx-apply-manifests-4gw6h   0/1     Error    0          20m
    hvst-upgrade-xtkwx-apply-manifests-55bll   0/1     Error    0          18m
    hvst-upgrade-xtkwx-apply-manifests-f4j8r   0/1     Error    0          19m
    hvst-upgrade-xtkwx-apply-manifests-f78gj   0/1     Error    0          20m
    hvst-upgrade-xtkwx-apply-manifests-fwjx2   0/1     Error    0          20m
    hvst-upgrade-xtkwx-apply-manifests-mjgkg   0/1     Error    0          10m
    hvst-upgrade-xtkwx-apply-manifests-nsnzb   0/1     Error    0          15m

    ```

1. The pod logs display `Current version is not supported. Abort the upgrade.` 
    ```
    harvester102:~ # kubectl -n harvester-system logs hvst-upgrade-xtkwx-apply-manifests-fwjx2
    harvester: v1.1.0
    harvesterChart: 1.1.0
    os: Harvester eeeb1be-dirty
    kubernetes: v1.23.10+rke2r1
    rancher: v2.6.4-harvester3
    monitoringChart: 100.1.0+up19.0.3
    loggingChart: 100.1.3+up3.17.7
    kubevirt: 0.54.0
    minUpgradableVersion: 'v1.0.3'
    rancherDependencies:
    fleet:
        chart: 100.0.3+up0.3.9
        app: 0.3.9
    fleet-crd:
        chart: 100.0.3+up0.3.9
        app: 0.3.9
    rancher-webhook:
        chart: 1.0.4+up0.2.5
        app: 0.2.5
    Current version: 1.0.2
    Minimum upgradable version: 1.0.3
    Current version is not supported. Abort the upgrade.
    ```

### Test Result 2
1. Can upgrade successfully from v1.0.3 to v1.1.0 with release tag 
    ![image](https://user-images.githubusercontent.com/29251855/193579438-17b74e97-9186-4572-8eaf-9918c3da0822.png)


### Test Result 3
1. Can upgrade successfully from v1.0.2 to v1.1.0 without release tag
    ![image](https://user-images.githubusercontent.com/29251855/193731628-768ffebb-f55f-4f41-98c7-98da7220b7c4.png)

