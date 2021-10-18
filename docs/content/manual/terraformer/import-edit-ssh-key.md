---
title: Import and make changes to ssh_key resource
---
1. Import ssh_key resource
`terraformer import harvester -r ssh_key`
1. Replace the provider (already explained in the installation process above)
terraform plan and apply command should print "No changes."
1. Alter the resource and check with terraform plan then terraform apply
1. For instance, alter the following properties: name, namespace and public_key in the ssh_key.tf file
1. Check the change through either the UI or the API

## Expected Results
- Import output
```
terraformer import harvester -r ssh_key
2021/08/04 16:14:36 harvester importing... ssh_key
2021/08/04 16:14:37 harvester done importing ssh_key
...
```
- Terraform plan output
```
name => Plan: 1 to add, 0 to change, 1 to destroy.
namespace => Plan: 1 to add, 0 to change, 1 to destroy.
public_key => Plan: 0 to add, 1 to change, 0 to destroy.
```
- You should see the changes on the UI in the according sections