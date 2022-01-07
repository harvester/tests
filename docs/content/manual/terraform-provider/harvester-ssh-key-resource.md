---
title: Test the harvester_ssh_key resource (e2e_be)
---
These following steps must be done for every resources, for avoiding repetitions, look at the detailed instructions at the beginning of the page.
1. Import a resource
1. Generates a speculative execution plan with terraform plan command
1. Create the resource with terraform apply command
1. Use terraform plan again
1. Use terraform apply again
1. Destroy the resource with the command terraform destroy

## Expected Results
1. The resource is well imported in the terraform.tfstate file and you can print it with the terraform show command
1. The command should display the difference between the actual status and the configured status
`Plan: 1 to add, 0 to change, 0 to destroy.`
`Apply complete! Resources: 1 added, 0 changed, 0 destroyed.`
1. You must see the new resource(s) on the Harvester dashboard`
1. `No changes. Your infrastructure matches the configuration.`
1. `Apply complete! Resources: 0 added, 0 changed, 0 destroyed.`
1. `Destroy complete! Resources: 1 destroyed.`
