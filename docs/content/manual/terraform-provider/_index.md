---
title: Terraform Provider
---
## Installation of Terraform with the Harvester Provider:
1. download and install terraform https://www.terraform.io/downloads.html
1. download and install terraform-provider-harvester https://github.com/harvester/terraform-provider-harvester#readme
1. test plan, apply, destory, import commands for each supported resource
https://github.com/harvester/terraform-provider-harvester/tree/master/docs
https://github.com/harvester/terraform-provider-harvester/tree/master/examples
## Write the provider.tf resource
## Take the following steps to test each resource:
You will find out all the needed example files here, https://github.com/harvester/terraform-provider-harvester/tree/master/examples
1. If a resource already exists, run the terraform import command to import it 
    - Example with the ssh_key resource: 
    `terraform import harvester_ssh_key.<mysshkey> <Namespace>/<mysshkey>`
Prior to running terraform import it is necessary to write a resource configuration block for the resource manually, to which the imported object will be attached.
Something like:
- ssh.tf
```
resource "harvester_ssh_key" "mysshkey" {
}
```
1. If the configuration is inconsistent with the actual resource status, run the terraform plan command to display the difference between the actual status and the configured status
1. Run terraform apply , no error, The actual status is consistent with the configuration
1. Run terraform plan again, no error, prompting No changes
1. Run terraform apply again, no error, prompting No changes
1. Run terraform destroy, no error, and the resource is deleted