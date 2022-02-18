---
title: #1218 Http proxy setting on harvester 
---

 * Related issue: [#1218](https://github.com/harvester/harvester/issues/1218) Missing http proxy settings on rke2 and rancher pod

## Environment setup
Setup an airgapped harvester
1. Clone ipxe example repository https://github.com/harvester/ipxe-examples 
2. Edit the `setting.xml` file under vagrant ipxe example
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
7. ssh to server node with user `rancher`
8. Run `kubectl create deployment nginx --image=nginx:latest` on Harvester cluster
9. Run `kubectl get pods`

## Expected Results
1. At Step 2, Can download and create image from URL without error
![image](https://user-images.githubusercontent.com/29251855/142995879-65d085ed-1e95-4cbc-af7f-d4017cd2ec8f.png)
2. At step 6, Can backup running VM to external S3 storage correctly
3. At step 6, Can delete backup from external S3 correctly
4. At step 9, Can pull image from internet and deploy nginx pod in running status
```
harvester-node-0:/home/rancher # kubectl create deployment nginx --image=nginx:latest
deployment.apps/nginx created
harvester-node-0:/home/rancher # kubectl get pods 
NAME                     READY   STATUS    RESTARTS   AGE
nginx-55649fd747-hkfjh   1/1     Running   0          28s
```
