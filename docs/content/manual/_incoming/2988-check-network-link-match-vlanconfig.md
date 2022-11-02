---
title: Check Network interface link status can match the available NICs in Harvester vlanconfig
---

* Related issues: [#2988](https://github.com/harvester/harvester/issues/2988) [BUG] Network interface link status judgement did not match the available NICs in Harvester vlanconfig
  
## Category: 
* Network

## Verification Steps
1. Create cluster network `cn1`
  ![image](https://user-images.githubusercontent.com/29251855/196580297-57541544-48f5-4492-b3e9-a3450697f490.png)
1. Create a vlanconfig `config-n1` on `cn1` which applied to node 1 only
  ![image](https://user-images.githubusercontent.com/29251855/196580491-0572c539-5828-4f2e-a0a6-59b40fcc549b.png)

1. Select an available NIC on the Uplink 
  ![image](https://user-images.githubusercontent.com/29251855/196580574-d38d59de-251c-4cf8-885d-655b76a78659.png)

4. Create a vlan, the cluster network `cn1` vlanconfig and provide valid vlan id `91`
  ![image](https://user-images.githubusercontent.com/29251855/196584602-b663ca69-da9a-42e3-94e0-41e094ff1d0b.png)

5. Edit `config-n1`, 
6. Check NICs list in Uplink 
7. ssh to node 1
8. Check the available NICs on Network config
![image](https://user-images.githubusercontent.com/29251855/197510924-b070f305-b6e4-477d-97b8-75006b264c30.png)
9. Check the state of linkmonitor nic on node1
    ```
    harv221021:~ # kubectl get linkmonitor nic -o yaml
    apiVersion: network.harvesterhci.io/v1beta1
    kind: LinkMonitor
    metadata:
        creationTimestamp: "2022-10-24T09:30:56Z"
        finalizers:
        - wrangler.cattle.io/harvester-network-link-monitor-controller
        generation: 4
        name: nic
        resourceVersion: "43501"
        uid: a23fd9b8-afae-4ced-92b7-6f5a25c70a3c
    spec:
        targetLinkRule:
        typeRule: device
    status:
        linkStatus:
        harv221021:
        - index: 2
            mac: 00:1b:21:38:5c:78
            name: enp179s0f0
            state: down
            type: device
        - index: 3
            mac: e4:54:e8:7c:f3:d4
            masterIndex: 6
            name: eno1
            state: up
            type: device
        - index: 4
            mac: 00:1b:21:38:5c:79
            name: enp179s0f1
            state: down
            type: device
    
    ```

10. Check the `ip link` status on node1
    ```
    harv221021:~ # ip link
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
        link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    2: enp179s0f0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN mode DEFAULT group default qlen 1000
        link/ether 00:1b:21:38:5c:78 brd ff:ff:ff:ff:ff:ff
    3: eno1: <BROADCAST,MULTICAST,SLAVE,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast master mgmt-bo state UP mode DEFAULT group default qlen 1000
        link/ether e4:54:e8:7c:f3:d4 brd ff:ff:ff:ff:ff:ff
        altname enp0s31f6
    4: enp179s0f1: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN mode DEFAULT group default qlen 1000
        link/ether 00:1b:21:38:5c:79 brd ff:ff:ff:ff:ff:ff
    5: mgmt-br: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000
        link/ether e4:54:e8:7c:f3:d4 brd ff:ff:ff:ff:ff:ff
    6: mgmt-bo: <BROADCAST,MULTICAST,MASTER,UP,LOWER_UP> mtu 1500 qdisc noqueue master mgmt-br state UP mode DEFAULT group default qlen 1000
        link/ether e4:54:e8:7c:f3:d4 brd ff:ff:ff:ff:ff:ff
    
    ```

11. Enable NIC `enp179s0f0` by plugging physical network cable
    ```
    harv221021:~ # ip a | grep enp179s0f*
    2: enp179s0f0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN group default qlen 1000
    4: enp179s0f1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    ```

12. Check the available NICs on Network config on node 1
  ![image](https://user-images.githubusercontent.com/29251855/197517224-9914f569-62d2-42c3-8339-57a76fa530e7.png)

13. Check the state of linkmonitor nic on node 1
    ```
    harv221021:~ # kubectl get linkmonitor nic -o yaml
    apiVersion: network.harvesterhci.io/v1beta1
    kind: LinkMonitor
    metadata:
    creationTimestamp: "2022-10-24T09:30:56Z"
    finalizers:
    - wrangler.cattle.io/harvester-network-link-monitor-controller
    generation: 5
    name: nic
    resourceVersion: "122674"
    uid: a23fd9b8-afae-4ced-92b7-6f5a25c70a3c
    spec:
    targetLinkRule:
        typeRule: device
    status:
    linkStatus:
        harv221021:
        - index: 2
        mac: 00:1b:21:38:5c:78
        name: enp179s0f0
        state: down
        type: device
        - index: 3
        mac: e4:54:e8:7c:f3:d4
        masterIndex: 6
        name: eno1
        state: up
        type: device
        - index: 4
        mac: 00:1b:21:38:5c:79
        name: enp179s0f1
        state: up
        type: device
    ```

14. check the `ip link` status on node 1
    ```
    harv221021:~ # ip link | grep enp179s*
    2: enp179s0f0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN mode DEFAULT group default qlen 1000
    4: enp179s0f1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
    ```

## Expected Results
1. The available NICs in Harvester vlanconfig can match the actual ip link status of all NICs
  ![image](https://user-images.githubusercontent.com/29251855/197522182-eacf449d-761a-43ba-807d-1ee8008fcbb1.png)

    ```
    harv221021:~ # ip link | grep enp179s*
    2: enp179s0f0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN mode DEFAULT group default qlen 1000
    4: enp179s0f1: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN mode DEFAULT group default qlen 1000
    ```

1. When we bring up specific NICs on node, the vlanconfig UI can also reflect the latest changes
![image](https://user-images.githubusercontent.com/29251855/197517224-9914f569-62d2-42c3-8339-57a76fa530e7.png)

    ```
    harv221021:~ # ip link | grep enp179s*
    2: enp179s0f0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN mode DEFAULT group default qlen 1000
    4: enp179s0f1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT group default qlen 1000
    ```

