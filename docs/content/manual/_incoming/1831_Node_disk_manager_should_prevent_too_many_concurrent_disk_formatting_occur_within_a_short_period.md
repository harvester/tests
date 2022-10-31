---
title: Node disk manager should prevent too many concurrent disk formatting occur within a short period
category: console
tags: dashboard, p2, functional
---
Ref: https://github.com/harvester/harvester/issues/1831


### Criteria
- [x] exceed the maximum, there should have requeue devices which equals the exceeds
- [x] hit the maximum, there should not have requeue devices
- [x] less than maximum, there should not have requeue devices

![image](https://user-images.githubusercontent.com/5169694/177324553-3b4800b2-9db9-45ec-a3cf-a630acb384cf.png)


### Verify Steps:
1. Install Harvester with any node having at least 6 additional disks
1. Login to console and execute command to update log level to `debug` and `max-concurrent-ops` to `1` (On KVM environment, we have to set to `1` to make sure the _requeuing_ will happen.)
    - `kubectl patch ds -n harvester-system harvester-node-disk-manager --type=json -p'[{"op":"replace", "path":"/spec/template/spec/containers/0/command", "value": ["node-disk-manager", "--debug", "--max-concurrent-ops", "1"]}]'`
1. Watching log output by executing `kubectl get pods -A | grep node-disk | awk '{system("kubectl logs -fn "$1" "$2)}'`
1. Login to dashboard then navigate and edit host to add more than `1` disks
1. In the console log, should display `Hit maximum concurrent count. Requeue device <device id>`
1. In the dashboard, disks should be added successfully.
1. Login to console and execute command to update log level to `debug` and `max-concurrent-ops` to `2`
    - `kubectl patch ds -n harvester-system harvester-node-disk-manager --type=json -p'[{"op":"replace", "path":"/spec/template/spec/containers/0/command", "value": ["node-disk-manager", "--debug", "--max-concurrent-ops", "2"]}]'`
1. Watching log output by executing `kubectl get pods -A | grep node-disk | awk '{system("kubectl logs -fn "$1" "$2)}'`
1. Login to dashboard then navigate and edit host to add `2` disks
1. In the console log, there should not display `Hit maximum concurrent count. Requeue device <device id>`
1. In the dashboard, disks should be added successfully.
1. Login to console and execute command to update log level to `debug`
    - `kubectl patch ds -n harvester-system harvester-node-disk-manager --type=json -p'[{"op":"replace", "path":"/spec/template/spec/containers/0/command", "value": ["node-disk-manager", "--debug"]}]'`
1. Watching log output by executing `kubectl get pods -A | grep node-disk | awk '{system("kubectl logs -fn "$1" "$2)}'`
1. Login to dashboard then navigate and edit host to add less than `5` disks
1. In the console log, there should not display `Hit maximum concurrent count. Requeue device <device id>`
1. In the dashboard, disks should be added successfully.
