---
title: Ksmd support merge_across_node on/off 
category: UI
tags: dashboard, p1, integration
---
Ref: https://github.com/harvester/harvester/issues/2827

![image](https://user-images.githubusercontent.com/5169694/193305898-48255477-1d19-48af-b132-3c019bd3f58b.png)
![image](https://user-images.githubusercontent.com/5169694/193314630-7add9b5a-2d9e-49cb-8d3a-1075531145e8.png)


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
1. Update <node1>'s **Ksmtuned** to check `Enable Merge Across Nodes`
1. Monitor data in Step.8 should reflect to:
    - `/sys/kernel/mm/ksm/run` should be updated to `2`
    - `/sys/kernel/mm/ksm/pages_*` should be updated to `0`
1. Restart all VMs scheduling to `<node1>`
1. Monitor data in Step.8 should reflect to:
    - `/sys/kernel/mm/ksm/run` should be updated to `1`
    - `/sys/kernel/mm/ksm/pages_*` should be updated and less than Step.8 monitored 
