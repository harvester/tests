---
title: Upgrade support of audit and event log
---

* Related issues: [#2750](https://github.com/harvester/harvester/issues/2750) [FEATURE] Upgrade support of audit and event log

  
## Category: 
* Logging Audit

## Verification Steps
1. Prepare v1.0.3 cluster, single-node and multi-node need to be tested separately
1. Upgrade to v1.1.0-rc2 / master-head
1. The upgrade should be successful, if not, check log and POD errors
1. After upgrade, check following PODs and files, there should be no error

## Expected Results

### Test Result 1: Singe node upgrade check

### Singe node upgrade check 
1. Check the following files and pods have no error 
1. logging related pods 
    ```
    n1-103:~ # kubectl get pods -n cattle-logging-system 
    NAME                                                      READY   STATUS      RESTARTS      AGE
    harvester-default-event-tailer-0                          1/1     Running     3 (39m ago)   69m
    rancher-logging-574448c578-lhvbd                          1/1     Running     3 (39m ago)   70m
    rancher-logging-kube-audit-fluentbit-7kq99                1/1     Running     3 (39m ago)   69m
    rancher-logging-kube-audit-fluentd-0                      2/2     Running     6 (39m ago)   70m
    rancher-logging-kube-audit-fluentd-configcheck-ac2d4553   0/1     Completed   0             70m
    rancher-logging-rke2-journald-aggregator-4f9jl            1/1     Running     3 (39m ago)   70m
    rancher-logging-root-fluentbit-tcd7z                      1/1     Running     3 (39m ago)   69m
    rancher-logging-root-fluentd-0                            2/2     Running     6 (39m ago)   69m
    rancher-logging-root-fluentd-configcheck-ac2d4553         0/1     Completed   0             70m
    ```

1. config file exists 
    ```
    n1-103:~ # cat /etc/rancher/rke2/config.yaml.d/90-harvester-server.yaml
    cni: multus,canal
    cluster-cidr: 10.52.0.0/16
    service-cidr: 10.53.0.0/16
    cluster-dns: 10.53.0.10
    tls-san:
        - 192.168.122.141
    audit-policy-file: /etc/rancher/rke2/config.yaml.d/92-harvester-kube-audit-policy.yaml
    ```
    ```
    n1-103:~ # cat /etc/rancher/rke2/config.yaml.d/92-harvester-kube-audit-policy.yaml
    apiVersion: audit.k8s.io/v1
    kind: Policy
    omitStages:
        - "ResponseStarted"
        - "ResponseComplete"
    rules:
        # Any include/exclude rules are added here
        # A catch-all rule to log all other (create/delete/patch) requests at the Metadata level
        - level: Metadata
        verbs: ["create", "delete", "patch"]
        omitStages:
            - "ResponseStarted"
            - "ResponseComplete"
    ```

1. /oem/99_custom.yaml is patched 
    ```
    n1-103:~ # grep "92-harvester" /oem/99_custom.yaml -5
                cluster-cidr: 10.52.0.0/16
                service-cidr: 10.53.0.0/16
                cluster-dns: 10.53.0.10
                tls-san:
                    - 192.168.122.141
                audit-policy-file: /etc/rancher/rke2/config.yaml.d/92-harvester-kube-audit-policy.yaml
                encoding: ""
                ownerstring: ""
            - path: /etc/rancher/rke2/config.yaml.d/90-harvester-agent.yaml
                permissions: 384
                owner: 0
    --
                    valuesContent: |-
                    flannel:
                        iface: harvester-mgmt
                encoding: ""
                ownerstring: ""
            - path: /etc/rancher/rke2/config.yaml.d/92-harvester-kube-audit-policy.yaml
                permissions: 384
                owner: 0
                group: 0
                content: |
                apiVersion: audit.k8s.io/v1
    ```
    ```
    vim /oem/99_custom.yaml
    
    - path: /etc/rancher/rke2/config.yaml.d/92-harvester-kube-audit-policy.yaml
                permissions: 384
                owner: 0
                group: 0
                content: |
                apiVersion: audit.k8s.io/v1
                kind: Policy
                omitStages:
                    - "ResponseStarted"
                    - "ResponseComplete"
                rules:
                    # Any include/exclude rules are added here
                    # A catch-all rule to log all other (create/delete/patch) requests at the Metadata level
                    - level: Metadata
                    verbs: ["create", "delete", "patch"]
                    omitStages:
                        - "ResponseStarted"
                        - "ResponseComplete"
                encoding: ""
                ownerstring: ""
    ```

### Test Result 2: Multi nodes upgrade check 
### Multi nodes upgrade check 
1. Check the following files and pods have no error 
1. logging related pods 
    ```
    n1-103:~ # kubectl get pods -n cattle-logging-system
    NAME                                             READY   STATUS    RESTARTS      AGE
    harvester-default-event-tailer-0                 1/1     Running   0             47m
    rancher-logging-574448c578-wv9wd                 1/1     Running   0             47m
    rancher-logging-kube-audit-fluentbit-dnxzr       1/1     Running   2 (38m ago)   59m
    rancher-logging-kube-audit-fluentbit-s9bfj       1/1     Running   2 (29m ago)   59m
    rancher-logging-kube-audit-fluentbit-snrml       1/1     Running   2 (49m ago)   59m
    rancher-logging-kube-audit-fluentd-0             2/2     Running   0             36m
    rancher-logging-rke2-journald-aggregator-c4kk4   1/1     Running   2 (49m ago)   59m
    rancher-logging-rke2-journald-aggregator-rc4gf   1/1     Running   2 (29m ago)   59m
    rancher-logging-rke2-journald-aggregator-sc56f   1/1     Running   2 (38m ago)   59m
    rancher-logging-root-fluentbit-fh9v9             1/1     Running   2 (49m ago)   59m
    rancher-logging-root-fluentbit-v65sz             1/1     Running   2 (38m ago)   59m
    rancher-logging-root-fluentbit-xkp8p             1/1     Running   2 (29m ago)   59m
    rancher-logging-root-fluentd-0                   2/2     Running   0             36m
    ```  
1. kube-audit files
1. Check the kube-apiserver has param of audit
    ```
        n1-103:~ # ps aux | grep kube-apiserver
        root      2819 41.7  2.6 3468424 2196848 ?     Ssl  12:25  56:05 kube-apiserver --audit-policy-file=/etc/rancher/rke2/config.yaml.d/92-harvester-kube-audit-policy.yaml --audit-log-path=/var/lib/rancher/rke2/server/logs/audit.log
    ```
1. The /var/lib/rancher/rke2/server/logs/audit.log have increasing content
    ```
    n1-103:~ # du -sh /var/lib/rancher/rke2/server/logs/audit.log
    8.0M	/var/lib/rancher/rke2/server/logs/audit.log
    
    n1-103:~ # du -sh /var/lib/rancher/rke2/server/logs/audit.log
    8.5M	/var/lib/rancher/rke2/server/logs/audit.log
    ```

1. config file exists 
    ```
    n1-103:~ # cat /etc/rancher/rke2/config.yaml.d/90-harvester-server.yaml
    cni: multus,canal
    cluster-cidr: 10.52.0.0/16
    service-cidr: 10.53.0.0/16
    cluster-dns: 10.53.0.10
    tls-san:
        - 192.168.50.199
    audit-policy-file: /etc/rancher/rke2/config.yaml.d/92-harvester-kube-audit-policy.yaml
    ```
    ```
    apiVersion: audit.k8s.io/v1
    kind: Policy
    omitStages:
        - "ResponseStarted"
        - "ResponseComplete"
    rules:
        # Any include/exclude rules are added here
        # A catch-all rule to log all other (create/delete/patch) requests at the Metadata level
        - level: Metadata
        verbs: ["create", "delete", "patch"]
        omitStages:
            - "ResponseStarted"
            - "ResponseComplete"
    
    ```
1. /oem/99_custom.yaml is patched 
    ```
    n1-103:~ # grep "92-harvester" /oem/99_custom.yaml -5
                cluster-cidr: 10.52.0.0/16
                service-cidr: 10.53.0.0/16
                cluster-dns: 10.53.0.10
                tls-san:
                    - 192.168.50.199
                audit-policy-file: /etc/rancher/rke2/config.yaml.d/92-harvester-kube-audit-policy.yaml
                encoding: ""
                ownerstring: ""
            - path: /etc/rancher/rke2/config.yaml.d/90-harvester-agent.yaml
                permissions: 384
                owner: 0
    --
                    valuesContent: |-
                    flannel:
                        iface: harvester-mgmt
                encoding: ""
                ownerstring: ""
            - path: /etc/rancher/rke2/config.yaml.d/92-harvester-kube-audit-policy.yaml
                permissions: 384
                owner: 0
                group: 0
                content: |
                apiVersion: audit.k8s.io/v1
    ```
    ```
    - path: /etc/rancher/rke2/config.yaml.d/92-harvester-kube-audit-policy.yaml
                permissions: 384
                owner: 0
                group: 0
                content: |
                apiVersion: audit.k8s.io/v1
                kind: Policy
                omitStages:
                    - "ResponseStarted"
                    - "ResponseComplete"
                rules:
                    # Any include/exclude rules are added here
                    # A catch-all rule to log all other (create/delete/patch) requests at the Metadata level
                    - level: Metadata
                    verbs: ["create", "delete", "patch"]
                    omitStages:
                        - "ResponseStarted"
                        - "ResponseComplete"
                encoding: ""
                ownerstring: ""
    ```


### Test Result 3: 
Check the UI of `Monitoring & Logging` work as in fresh installed cluster after upgrade to `v1.1.0-rc2`

1. Cluster Outputs
    ![image](https://user-images.githubusercontent.com/29251855/195548105-8c303a21-77b6-4d27-b127-314579f3dd0c.png)

1. Cluster Flows
    ![image](https://user-images.githubusercontent.com/29251855/195548149-cd95cca6-76b5-421c-ae4a-ee8fc37746bf.png)

1. Logging configuration
    ![image](https://user-images.githubusercontent.com/29251855/195548206-7f68ba92-ae86-4809-87fd-bf1ed07ec9cd.png)

1. Outputs
    ![image](https://user-images.githubusercontent.com/29251855/195549147-181b5e76-27ae-42db-a233-b6d68b5c9143.png)

1. Flow
    ![image](https://user-images.githubusercontent.com/29251855/195549228-58786461-0023-4d26-8536-1025d50a7346.png)

1. Monitoring configuration - Altermanager
    ![image](https://user-images.githubusercontent.com/29251855/195549422-012c950a-b75f-45e9-b700-2dc41241a23c.png)

1. Altermanager config
    ![image](https://user-images.githubusercontent.com/29251855/195549652-96786120-3867-4245-bda8-bfd56d8968d4.png)
    ![image](https://user-images.githubusercontent.com/29251855/195552086-cae1be22-5760-444a-bf73-9480246bc9e4.png)


