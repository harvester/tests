---
title: #1218 Http proxy setting pull and deploy application	
---

[#1218](https://github.com/harvester/harvester/issues/1218) Http proxy setting pull and deploy application

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
2. ssh to server node with user `rancher`
3. Run `kubectl create deployment nginx --image=nginx:latest` on Harvester cluster
4. Run `kubectl get pods`

## Expected Results
1. Can pull image from internet and deploy nginx pod in running status
```
harvester-node-0:/home/rancher # kubectl create deployment nginx --image=nginx:latest
deployment.apps/nginx created
harvester-node-0:/home/rancher # kubectl get pods 
NAME                     READY   STATUS    RESTARTS   AGE
nginx-55649fd747-hkfjh   1/1     Running   0          28s
```
