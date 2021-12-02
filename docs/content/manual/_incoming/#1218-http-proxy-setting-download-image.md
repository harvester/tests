---
title: #1218 Http proxy setting download image	
---

[#1218](https://github.com/harvester/harvester/issues/1218) Http proxy setting download image

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

## Expected Results
1. Can download and create image from URL without error
![image](https://user-images.githubusercontent.com/29251855/142995879-65d085ed-1e95-4cbc-af7f-d4017cd2ec8f.png)
