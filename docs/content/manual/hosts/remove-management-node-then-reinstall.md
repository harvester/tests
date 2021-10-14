---
title: Remove a management node from a 3 nodes cluster and add it back to the cluster by reinstalling it
---
1. From a HA cluster with 3 nodes
2. Delete one of the nodes after the node promotion(all 3 nodes are management nodes)
3. Reinstall the removed node with the same node name and IP
4. The rejoined node will be promoted to master automatically

## Expected Results
1. The removed node should be able to rejoin the cluster without issues

### Comments
- Purpose is to cover this scenario: https://github.com/harvester/harvester/issues/1040
- Check the job promotion with the command kubectl get jobs -n harvester-system
- If a node is stuck in the removing status, you likely face to this issue, execute this command as workaround: `kubectl get node -o name <nodename> | xargs -i kubectl patch {} -p '{"metadata":{"finalizers":[]}}' --type=merge`