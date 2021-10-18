---
title: Target Harvester with the default kubeconfig located in $HOME/.kube/config
---
1. Make sure the kubeconfig is defined in the file `$HOME/.kube/config`
1. Check if you can interact with the Harvester by creating resource like a SSH key
1. Execute the `terraform apply` command

## Expected Results
1. The resource should be created
`Apply complete! Resources: 1 added, 0 changed, 0 destroyed.`
1. Check if you can see your resource in the Harvester WebUI