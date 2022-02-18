---
title: Shut down host in maintenance mode and verify label change
---

* Related issues: [#1272](https://github.com/harvester/harvester/issues/1272) Shut down a node with maintenance mode should show red label

## Verification Steps

1. Open host page
1. Set a node to maintenance mode
1. Turn off host vm of the node
1. Check node status
1. Turn on host
1. Check node status

## Expected Results
1. The node should go into maintenance mode
1. The node label should go red
1. When turned on the node status should go back to yellow