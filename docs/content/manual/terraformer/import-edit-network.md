---
title: Import and make changes to network resource
---
1. Import network resource
`terraformer import harvester -r network`
1. Replace the provider (already explained in the installation process above)
1. terraform plan and apply command should print "No changes."
1. Alter the resource and check with terraform plan then terraform apply
For instance, alter the following properties: name, namespace and vlan_id in the network.tf file
1. Check the change through either the UI or the API

## Expected Results
- Import output
```
terraformer import harvester -r network
2021/08/04 16:14:08 harvester importing... network
2021/08/04 16:14:08 harvester done importing network
...
```
- Terraform plan output
```
name => Plan: 1 to add, 0 to change, 1 to destroy.
namespace => Plan: 1 to add, 0 to change, 1 to destroy.
vlan_id => Plan: 0 to add, 1 to change, 0 to destroy.
```
- You should see the changes on the UI in the according sections