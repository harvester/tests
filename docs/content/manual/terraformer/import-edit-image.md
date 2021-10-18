---
title: Import and make changes to image resource
---
1. Import image resource
`terraformer import harvester -r image`
1. Replace the provider (already explained in the installation process above)
terraform plan and apply command should print "No changes."
1. Alter the resource and check with terraform plan then terraform apply
For instance, alter the following properties: description, display_name, name, namespace and url in the image.tf file
1. Check the change through either the UI or the API

## Expected Results
- Import output
```
terraformer import harvester -r image
2021/08/04 16:14:52 harvester importing... image
2021/08/04 16:14:52 harvester done importing image
...
```
- Terraform plan output
```
description => Plan: 0 to add, 1 to change, 0 to destroy.
display_name => Plan: 0 to add, 1 to change, 0 to destroy.
name => Plan: 1 to add, 0 to change, 1 to destroy.
namespace => Plan: 1 to add, 0 to change, 1 to destroy.
url => Plan: 0 to add, 1 to change, 0 to destroy.
```
- You should see the changes on the UI in the according sections