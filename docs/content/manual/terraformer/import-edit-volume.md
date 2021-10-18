---
title: Import and make changes to volume resource
---
1. Import volume resource
`terraformer import harvester -r volume`
1. Replace the provider (already explained in the installation process above)
terraform plan and apply command should print "No changes."
1. Alter the resource and check with terraform plan then terraform apply
For instance, alter the following properties: name, namespace in the volume.tf file
1. Check the change through either the UI or the API
## Expected Results
- Import output
```
terraformer import harvester -r volume
2021/08/04 16:15:29 harvester importing... volume
2021/08/04 16:15:29 harvester done importing volume
...
```
- Terraform plan output
```
name => Plan: 1 to add, 0 to change, 1 to destroy.
namespace => Plan: 1 to add, 0 to change, 1 to destroy.
```
- You should see the changes on the UI in the according sections