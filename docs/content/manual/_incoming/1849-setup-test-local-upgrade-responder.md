---
title: Setup and test local Harvester upgrade responder
---

* Related issues: [#1849](https://github.com/harvester/harvester/issues/1849) [Task] Improve Harvester upgrade responder

## Category: 
* Upgrade

## Verification Steps
Follow the steps in https://github.com/harvester/harvester/issues/1849#issuecomment-1180346017

1. Clone [longhorn/upgrade-responder](https://github.com/longhorn/upgrade-responder) and checkout to [v0.1.4](https://github.com/longhorn/upgrade-responder/releases/tag/v0.1.4).
1. Edit [response.json](https://github.com/longhorn/upgrade-responder/blob/master/config/response.json) content in config folder
  ```
  {
    "Versions": [
      {
        "Name": "v1.0.2-master-head",
        "ReleaseDate": "2022-06-15T00:00:00Z",
        "Tags": [
          "latest",
          "test",
          "dev"
        ]
      }
    ]
  }
  
  ```
1. Install InfluxDB  
1. Run longhorn/upgrade-responder with the command:
  ```
  go run main.go --debug start --upgrade-response-config config/response.json --influxdb-url http://localhost:8086 --geodb geodb/GeoLite2-City.mmdb --application-name harvester
  ```
1. Check the local upgrade responder is running
  ```
  curl -X POST http://localhost:8314/v1/checkupgrade \
       -d '{ "appVersion": "v1.0.2", "extraInfo": {}}'
  ```
1. Create a new folder `v1.0.2-master-head` for the http server 
1. Download the latest master head installation files 
https://releases.rancher.com/harvester/master/harvester-master-amd64.iso
https://releases.rancher.com/harvester/master/harvester-master-initrd-amd64
https://releases.rancher.com/harvester/master/harvester-master-rootfs-amd64.squashfs
https://releases.rancher.com/harvester/master/harvester-master-vmlinuz-amd64
https://releases.rancher.com/harvester/master/harvester-master-amd64.sha256

1. Launch a python http server 
```
python3 -m http.server
```
1. Create a `version.yaml` with the following content 
```
apiVersion: harvesterhci.io/v1beta1
kind: Version
metadata:
  name: v1.0.2-master-head
  namespace: harvester-system
spec:
  isoChecksum: '0d5999471553e767cb0c4d7d1c82b00b884e994e5856d8feb90798ace523b7aa2145a5fc245e1d0073ce7b41c490979950f3f31f60a682c971aba63d562973e5'
  isoURL: http://192.168.122.224:8000/v1.0.2-master-head/harvester-master-amd64.iso
  releaseDate: '20220712'
```
1. Check the upgrade responder connection in harvester node 
  ```
  curl -X POST http://192.168.122.224:8314/v1/checkupgrade      -d '{ "appVersion": "v1.0.2", "extraInfo": {}}'
  ```
1. Check the iso download url connection in harvester node 
  ```
  curl -output http://192.168.122.224:8000/harvester-master-amd64.iso
  ```
1. Open Harvester settings, change upgrade-checker-url setting to our upgrade-responder URL.
  ![image](https://user-images.githubusercontent.com/29251855/178421503-bce7d8a2-1c02-403d-ae10-0c073fd2c8b0.png)
1. Change the release download url to our http server url  
  ![image](https://user-images.githubusercontent.com/29251855/178421631-2c88cdc5-a138-403b-98b0-d944b01861ef.png)
1. ssh to harvester node, change to root, run `k9s`
1. Run : deployments -> / harvester -> select the harvester node 
1. Remove pods in deployment harvester-system/harvester to trigger check new versions.
![image](https://user-images.githubusercontent.com/29251855/178243762-fafc1c66-a3a2-4553-8aca-fb239da85677.png)
1. Wait for 5 - 10 minutes, 
1. Check Harvester dashboard and click the upgrade button 
![image](https://user-images.githubusercontent.com/29251855/178248176-8f0a2d80-cb96-43ca-976a-7e47b5f89244.png)
1. Select the version and start the upgrade process

## Expected Results
* Can select the prompted upgrade button by using the updated version of Harvester upgrade responder https://github.com/longhorn/upgrade-responder (v0.1.4) by using the `upgrade-checker url`
![image](https://user-images.githubusercontent.com/29251855/178421998-c2ad04e8-d912-46a0-8c35-dfd051aa0e86.png)

* Can correctly connect to the file server by using the `release URL` setting
![image](https://user-images.githubusercontent.com/29251855/178422307-322553f0-c783-4529-a97b-803a8e2e03a7.png)
