---
title: Alertmanager supports main stream receivers
--- 

* Related issues: [#2521](https://github.com/harvester/harvester/issues/2521) [FEATURE] Alertmanager supports main stream receivers

  
## Category: 
* Alter manager

## Verification Steps
1. Prepare another VM or machine have the same subnet with the Harvester 
1. Prepare a webhook server on the VM, reference to https://github.com/w13915984028/harvester-develop-summary/blob/main/test-log-event-audit-with-webhook-server.md
1. You may need to install python3 web package, refer to https://webpy.org/install
1. Run `export PORT=8094` on the webhook server VM 
1. Launch the webhook server `python3 simple-webhook-server.py` 
    ```
    davidtclin@ubuntu-clean:~$ python3 simple-webhook-server.py
    usage: export PORT=1234 to set http server port number as 1234
    start a simple webhook server, PORT 8094 @ 2022-09-21 16:39:58.706792 

    http://0.0.0.0:8094/
    ```
1. Access Harvester `Alertmanager Configs` page in Monitoring 
1. Create an Alertmanager config 
    ![image](https://user-images.githubusercontent.com/29251855/191452211-9892187b-4af2-4f73-8d34-19fedcd830b8.png)
1. Access the created Alertmanager config 
1. Click Add receiver 
    ![image](https://user-images.githubusercontent.com/29251855/191452302-929fe806-6485-4837-be84-f2814c28d4ac.png)
1. Select webhook page 
1. Click Add webhook
    ![image](https://user-images.githubusercontent.com/29251855/191452393-de222b27-9d0a-4dc5-bed0-e9c449b95766.png)
1. Add `http://server_ip:8094 to the URL 
    ![image](https://user-images.githubusercontent.com/29251855/191458438-98d3e36d-27af-4f26-aaf4-c910036ed124.png)
1. Access Harvester node 
1. Run `kubectl get alertmanagerconfig -A -o yaml`
1. Check the webhook server have applied to the `Altertmanagerconfig` pod 
1. Check the webhook receiver can be created 
    ![image](https://user-images.githubusercontent.com/29251855/191464505-d1a2d718-a742-4072-853a-a4c221abe97a.png)

Refer to HEP document for more details 
https://github.com/w13915984028/harvester/blob/fix2517/enhancements/20220720-alertmanager.md 

## Expected Results
1. We can add `webhook` type receiver from the `Altermanager Config` page for the given namespace
    ![image](https://user-images.githubusercontent.com/29251855/191467324-220f4e30-53fe-4893-963b-439b5dd8446b.png)

    ![image](https://user-images.githubusercontent.com/29251855/191467902-9a38f735-038a-40c6-94e5-462e48aa1bcf.png)

1. Can applied the changes to `alertmanagerconfig` pod in Harveser
    ```
    harv0921:~ # kubectl get alertmanagerconfig -A -o yaml
    apiVersion: v1
    items:
    - apiVersion: monitoring.coreos.com/v1alpha1
    kind: AlertmanagerConfig
    metadata:
        creationTimestamp: "2022-09-21T08:16:21Z"
        generation: 1
        name: alert-receiver
        namespace: default
        resourceVersion: "14566"
        uid: 8f9c30a2-42c1-4831-92b5-8abf71134333
    spec:
        receivers: []
        route:
        groupBy: []
        groupInterval: 5m
        groupWait: 30s
        matchers: []
        repeatInterval: 4h
    - apiVersion: monitoring.coreos.com/v1alpha1
    kind: AlertmanagerConfig
    metadata:
        creationTimestamp: "2022-09-21T08:48:38Z"
        generation: 2
        name: alertmanager
        namespace: default
        resourceVersion: "39171"
        uid: 32f813c3-24fd-4faf-a270-1e7723a5dfdf
    spec:
        receivers:
        - name: webhook
        webhookConfigs:
        - httpConfig:
            tlsConfig: {}
            sendResolved: false
            url: http://192.168.122.230:8094
        route:
        groupBy: []
        groupInterval: 5m
        groupWait: 30s
        matchers: []
        repeatInterval: 4h
    kind: List
    metadata:
    resourceVersion: ""
    selfLink: ""

    ```