---
title: #1218 Http proxy setting backup to external S3
---

 [#1218](https://github.com/harvester/harvester/issues/1218) Http proxy setting backup to external S3

## Environment setup
Setup an airgapped harvester
1. Fetch ipxe vagrant example with new offline feature
https://github.com/harvester/ipxe-examples/pull/32 
2. Edit the setting.xml file
3. Set offline: `true`
4. Use ipxe vagrant example to setup a 3 nodes cluster


## Verification Steps
1. Open Settings, edit `http-proxy` with the following values
```
HTTP_PROXY=http://proxy-host:port
HTTPS_PROXY=http://proxy-host:port
NO_PROXY=localhost,127.0.0.1,0.0.0.0,10.0.0.0/8,192.168.0.0/16,cattle-system.svc,.svc,.cluster.local,<internal domain>
```
2. Create image from URL (change folder date to latest)
https://cloud-images.ubuntu.com/focal/20211122/focal-server-cloudimg-amd64.img 
3. Create a virtual machine 
4. Prepare an S3 account with `Bucket`, `Bucket region`, `Access Key ID` and `Secret Access Key`
5. Setup backup target in settings
6. Edit virtual machine and take backup

## Expected Results
1. Can backup running VM to external S3 storage correctly
2. Can delete backup from external S3 correctly
