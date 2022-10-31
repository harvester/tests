---
title: Enabling and Tuning KSM
category: UI
tags: dashboard, p1, integration
---
Ref: https://github.com/harvester/harvester/issues/2302


### Verify Steps:
1. Install Harvester with any nodes
1. Login to Dashboard and Navigate to hosts
1. Edit _node1_'s **Ksmtuned** to `Run` and **ThresCoef** to `85` then Click **Save**
1. Login to _node1_'s console, execute `kubectl get ksmtuned -oyaml --field-selector metadata.name=<node1>`
1. Fields in `spec` should be the same as Dashboard configured
1. Create an image for VM creation
1. Create multiple VMs with 2Gi+ memory and schedule on `<node1>` (memory size reflect to <node1>'s maximum size, total of VMs' memory should greater than 40%) 
1. Execute `watch -n1 grep . /sys/kernel/mm/ksm/*` to monitor ksm's status change
    - `/sys/kernel/mm/ksm/run` should be update to `1` after VMs started
    - `/sys/kernel/mm/ksm/page_*` should updating continuously
1. Login to Dashboard then navigate to _Hosts_, click <node1>
1. In the Tab of **Ksmtuned**, values in Statistics section should not be `0`.  (data in this section will be updated per min, so it not equals to console's output was expected.)
1. Stop all VMs scheduling to `<node1>`, the monitor data `/sys/kernel/mm/ksm/run` should be update to `0` (this is expected as it is designed to dynamically spawn ksm up when `ThresCoef` hits)
1. Update <node1>'s **Ksmtuned** to `Run: Prune`
1. Monitor data in Step.8 should reflect to:
    - `/sys/kernel/mm/ksm/run` should be update to `2`
    - `/sys/kernel/mm/ksm/pages_*` should be update to `0`
1. Update <node1>'s **Ksmtuned** to `Run: Stop`
1. Monitor data in Step.8 should reflect to:
    - `/sys/kernel/mm/ksm/run` should be update to `0`
