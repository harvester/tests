---
title: Terraform import VLAN
---

* Related issues: [#2261](https://github.com/harvester/harvester/issues/2261) [FEATURE] enhance terraform network to not pruge route_cidr and route_gateway


## Category: 
* Terraform

## Verification Steps

1. Install Harvester with any nodes
1. Install terraform-harvester-provider (using master-head for testing)
1. Execute `terraform init`
1. Create the file network.tf as following snippets, then execute `terraform import harvester_clusternetwork.vlan vlan` to import default vlan settings
```
resource "harvester_clusternetwork" "vlan" {
  name                 = "vlan"
  enable               = true
  default_physical_nic = "harvester-mgmt"
}
resource "harvester_network" "vlan1" {
  name      = "vlan1"
  namespace = "harvester-public"

  vlan_id = 1
  route_mode = "auto"
}
```
1. execute `terraform apply`
1. Login to dashboard then navigate to Advanced/Networks, make sure the Route Connectivity becomes Active
1. Execute `terraform apply` again and many more times

## Expected Results
1. Resources should not be changed or added or destroyed.