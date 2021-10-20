---
title: Import and make changes to virtual machine resource
---
1. Import virtual machine resource
`terraformer import harvester -r virtualmachine`
1. Replace the provider (already explained in the installation process above)
1. terraform plan and apply command should print "No changes."
1. Alter the resource and check with terraform plan then terraform apply
1. For instance, alter the following properties: cpu, memory, name in the virtualmachine.tf file
1. Check the change through either the UI or the API

## Expected Results
- Import output
```
terraformer import harvester -r virtualmachine
2021/08/04 16:15:08 harvester importing... virtualmachine
2021/08/04 16:15:09 harvester done importing virtualmachine
...
```
- Terraform plan output
```
cpu => Plan: 0 to add, 1 to change, 0 to destroy.
memory => Plan: 0 to add, 1 to change, 0 to destroy.
name => Plan: 1 to add, 0 to change, 1 to destroy.
namespace => Plan: 1 to add, 0 to change, 1 to destroy.
```
- You should see the changes on the UI in the according sections