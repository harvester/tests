---
title: Agent Node should not rely on specific master Node
---
Ref: https://github.com/harvester/harvester/issues/1521

## Verify Items
  - Agent Node should keep connection when any master Node is down

## Case: Agent Node's connecting status
1. Install Harvester with 4 nodes which joining node MUST join by VIP (point `server-url` to use VIP)
1. Make sure all nodes are ready
    1. Login to dashboard, check host **state** become `Active`
    1. SSH to the 1st node, run command `kubectl get node` to check all **STATUS** should be `Ready`
1. SSH to agent nodes which **ROLES** IS `<none>` in **Step 2i**'s output
   - [x] Output should contains VIP in the server URL, by run command `cat /etc/rancher/rke2/config.yaml.d/90-harvester-vip.yaml`
   - [x] Output should contain the line `server: https://127.0.0.1:6443`, by run command `cat /var/lib/rancher/rke2/agent/kubelet.kubeconfig`
   - [x] Output should contain the line `server: https://127.0.0.1:6443`, by run command `cat /var/lib/rancher/rke2/agent/kubeproxy.kubeconfig`
1. SSH to server nodes which **ROLES** contains `control-plane` in **Step 2i**'s output
    - [x] Check file should not exist in the path `/etc/rancher/rke2/config.yaml.d/90-harvester-vip.yaml`
1. Shut down a server node, check following things
    - [x] Host **State** should not be `Active` in dashboard
    - [x] Node **STATUS** should be `NotReady` in the command output of  `kubectl get node`
    - [x] **STATUS** of agent nodes should be `Ready` in the command output of  `kubectl get node`
1. Power on the server node, wait until it back to cluster
1. repeat **Step 5-6** for other server nodes