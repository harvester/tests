---
title: Test a deployment with ALL resources at the same time	
---
1. Re-use the previous generated TF files and group them all either in one directory or in the same file
1. Generates a speculative execution plan with terraform plan command
1. Create the resources with terraform apply command
1. Check that all resources are correctly created/running on the Harvester cluster
1. Destroy the resources with the command terraform destroy

## Expected Results
Refer to the harvester_ssh_key resource expected results	