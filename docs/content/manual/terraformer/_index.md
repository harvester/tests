---
title: Terraformer
---
## Introduction
Terraformer is a CLI tool that generates tf/json and tfstate files based on existing infrastructure, a reverse Terraform.
Of course, the tool needs a ready harvester cluster to be able to import resources.
Feature introduced by https://github.com/harvester/harvester/issues/943
## Installation
1. Download terraformer from releases https://github.com/harvester/terraformer/releases 

### Terraformer installation
```er/releases/download/v0.1.0-harvester/terraformer-harvester-linux-amd64
chmod +x terraformer-harvester-linux-amd64
sudo mv terraformer-harvester-linux-amd64 /usr/local/bin/terraformer
```
Make sure to set the env variable KUBECONFIG with the path or your kubeconfig file, check that the cluster ip is correct in the kubeconfig file. In my case, it was set to localhost so I had to change it.

1. Use terraformer to generate tf files and tfstates file from existing resources (example: only import image default/image-6skr8 and harvester-public/image-9lspw)
### Import resources
```
terraformer import harvester -r image -f image=default/image-6skr8:harvester-public/image-9lspw

# Or import all the images:
terraformer import harvester -r image
Replace the provider to registry.terraform.io/harvester/harvester
cd generated/harvester/image
vim provider.tf (add source  = "registry.terraform.io/harvester/harvester" to terraform.required_providers.harvester)
terraform state replace-provider "registry.terraform.io/-/harvester" "registry.terraform.io/harvester/harvester"
```
1. Use the tf files and tfstate files to manage the existing resources.
```
terraform init
terraform plan
terraform apply
```
### Supported Resources
- clusternetwork
- network
- ssh_key
- image
- virtualmachine
- volume