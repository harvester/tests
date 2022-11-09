---
title: Harvester supports event log
category: console
tag: dashboard, p1, integration
---
Ref: https://github.com/harvester/harvester/issues/2748

Verified this feature has been implemented.


Test Information
----
* Environment: **qemu/KVM 3 nodes**
* Harvester Version: **master-250f41e4-head**
* **ui-source** Option: **Auto**

### Verify Steps:
1. Install _Graylog_ via docker[^1]
1. Install Harvester with any nodes
1. Login to Dashboard then navigate to _Monitoring & Logging/Logging_
1. Create **Cluster Output** with following:
    - **Name**: gelf-evts
    - **Type**: `Logging/Event`
    - **Output**: GELF
    - **Target**: `<Graylog_IP>, <Graylog_Port>, <UDP>`
1. Create **Cluster Flow** with following:
    - **Name**: gelf-flow
    - **Type** of Matches: `Event`
    - **Cluster Outputs**: `gelf-evts`
1. Create an Image for VM creation
1. Create a vm `vm1` and start it
1. Login to `Graylog` dashboard then navigate to search
1. Select update frequency
![image](https://user-images.githubusercontent.com/5169694/191725169-d1203674-13d8-487b-9fa2-e1d9394fa5c0.png)
1. New logs should be posted continuously.


### code snippets to setup Graylog
```bash
docker run --name mongo -d mongo:4.2.22-rc0
sysctl -w vm.max_map_count=262145
docker run --name elasticsearch -p 9200:9200 -p 9300:9300 -e xpack.security.enabled=false  -e node.name=es01 -it docker.elastic.co/elasticsearch/elasticsearch:6.8.23
docker run --name graylog --link mongo --link elasticsearch -p 9000:9000 -p 12201:12201 -p 1514:1514 -p 5555:5555 -p 12202:12202 -p 12202:12202/udp -e GRAYLOG_PASSWORD_SECRET="Graypass3WordMor!e" -e GRAYLOG_ROOT_PASSWORD_SHA2=899e9793de44cbb14f48b4fce810de122093d03705c0971752a5c15b0fa1ae03   -e GRAYLOG_HTTP_EXTERNAL_URI="http://127.0.0.1:9000/"  -d graylog/graylog:4.3.5
```
- Login to _Graylog_ dashboard by the URL `http://<server_ip>:9000/` with `admin`/`ROOT_PASSWORDa1`
- Navigate to _System/Inputs_ then select input **GELF UDP**, update the port to `12202`
![image](https://user-images.githubusercontent.com/5169694/191723749-7d796243-5996-4884-90b4-d8227f81adc5.png)

