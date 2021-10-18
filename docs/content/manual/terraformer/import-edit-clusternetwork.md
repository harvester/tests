---
title: Import and make changes to clusternetwork resource
---
1. Import clusternetwork resource
```
terraformer import harvester -r clusternetwork
```
1. Replace the provider (already explained in the installation process above)
1. terraform plan and apply command should print "No changes."
1. Alter the resource and check with terraform plan then terraform apply
For instance, alter the following properties: default_physical_nic, enable in the clusternetwork.tf file
1. Check the change through either the UI or the API

## Expected Results
- Import output
```
terraformer import harvester -r clusternetwork
2021/08/04 15:43:25 harvester importing... clusternetwork
2021/08/04 15:43:26 harvester done importing clusternetwork
...
```
- Terraform plan output
```
default_physical => Plan: 0 to add, 1 to change, 0 to destroy.
enable=> Plan: 0 to add, 1 to change, 0 to destroy.
```
- You should see the changes on the UI in the according sections