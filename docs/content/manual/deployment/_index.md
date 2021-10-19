---
title: Deployment Tests for Harvester
---
# Installation
- ISO installation - Get the images from https://github.com/harvester/harvester/releases
- PXE boot installation - https://docs.harvesterhci.io/v0.2/install/pxe-boot-install/
- Rancher app deployment for development purpose
## How to Test Harvester Master
1. For harvester-installer tests, we can download the latest ISO from https://releases.rancher.com/harvester/master/harvester-amd64.iso that is built with a daily CRON job.
2. For the harvester server, just replace the harvester image with `master-head` on the harvester-system namespace, if u have only a single node u can delete the replicaset to restart the pod e.g, (kubectl delete rs harvester-xxxxx) 
    - `kubectl patch deployment harvester -p '{"spec": {"template": {"spec": {"containers": [{"image:": "rancher/harvester:master-head" }]}}}' -n harvester-system`
    - check and apply the latest CRDs from the master branch if needed.
    https://github.com/harvester/harvester/tree/master/deploy/charts/harvester/crds 
## Reference for the Harvester configuration
https://docs.harvesterhci.io/v0.3/install/harvester-configuration/
```
token: token
os:
  ssh_authorized_keys:
  - Write your public ssh key here
  modules:
    - kvm
    - nvme
  sysctl:
    kernel.printk: "4 4 1 7"
    kernel.kptr_restrict: "1"
  dns_nameservers:
    - 8.8.8.8
    - 1.1.1.1
  ntp_servers:
    - 0.us.pool.ntp.org
    - 1.us.pool.ntp.org
  password: rancher
  environment:
    test_env: test_env
  write_files:
  - encoding: ""
    content: test content
    owner: root
    path: /etc/test.txt
    permissions: '0755'
install:
  debug: true
  poweroff: true
```
---
