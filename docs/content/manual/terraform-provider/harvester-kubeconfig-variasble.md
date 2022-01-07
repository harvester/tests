---
title: Target Harvester by setting the variable kubeconfig with your kubeconfig file in the provider.tf file (e2e_be)
---
1. Define the kubeconfig variable in the provider.tf file
```
terraform {
  required_providers {
    harvester = {
      source  = "registry.terraform.io/harvester/harvester"
      version = "~> 0.1.0"
    }
  }
}
 
provider "harvester" {
  kubeconfig = "/path/of/my/kubeconfig"
}
```
1. Check if you can interact with the Harvester by creating resource like a SSH key
1. Execute the `terraform apply` command

## Expected Results
1. The resource should be created
`Apply complete! Resources: 1 added, 0 changed, 0 destroyed.`
1. Check if you can see your resource in the Harvester WebUI
