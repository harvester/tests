---
title: Terraform Rancher2 Provider Testing
category: Terraform
tag: integration
---
Ref: https://github.com/rancher/terraform-provider-rancher2/issues/1009


Test Information
----
* Environment Rancher: v2.7.X
* Environment for Harvester: bare-metal or qemu
* Harvester Version: v1.1.X
* **ui-source** Option: **Auto**
* Rancher2 Terraform Provider Plugin: v3.0.X [rancher2](https://github.com/rancher/terraform-provider-rancher2/releases)

### Test Setup Rancher2 Terraform Provider:
1. make sure terraform is installed at version equal or greater than 1.3.9, ie: `sudo apt install terraform`
1. utilize the [setup-provider.sh](https://github.com/rancher/terraform-provider-rancher2/blob/master/setup-provider.sh) script from the rancher2 terraform provider repo if testing an rc it would look something like `./setup-provider.sh rancher2 v3.0.0-rc1`
1. ensure the provider is installed, can cross check the directory structures under `~/.terraform.d/plugins/terraform.local`

### Setup Rancher v2.7.X
1. build an API Key for Rancher utilizing [this doc](https://ranchermanager.docs.rancher.com/reference-guides/user-settings/api-keys), keeping reference of the: access-key, secret-key, & bearer token
1. import a harvester cluster into Rancher v2.7.X, keep reference of that Harvester cluster name

## Additional Setup
1. build out a temporary directory to preform this deep integration testing
1. create the following two folders of something like:
    - `harvester-setup`
    - `rancher-setup`
1. inside each folder create a:
    - `main.tf`
    - `provider.tf`

### Harvester Setup
1. download the Harvester kubeconfig file into the `harvester-setup` folder
2. inside the `harvester-setup` folder in the `provider.tf` file add:
```
terraform {
  required_version = ">= 0.13"
  required_providers {
    harvester = {
      source  = "harvester/harvester"
      version = "0.6.1"
    }
  }
}

provider "harvester" {
  kubeconfig = "<the kubeconfig file path of the harvester cluster>"
}
```
3. inside the `main.tf` file in the `harvester-setup` folder add:
```
resource "harvester_image" "opensuse-leap" {
  name      = "opensuse-leap-15-4"
  namespace = "harvester-public"

  display_name = "openSUSE-Leap-15.4.x86_64-NoCloud.qcow2"
  source_type  = "download"
  url          = "https://download.opensuse.org/repositories/Cloud:/Images:/Leap_15.4/images/openSUSE-Leap-15.4.x86_64-NoCloud.qcow2"
}

data "harvester_clusternetwork" "mgmt" {
  name = "mgmt"
}

resource "harvester_network" "mgmt-vlan1" {
  name      = "mgmt-vlan1"
  namespace = "harvester-public"

  vlan_id = 1

  route_mode           = "auto"
  route_dhcp_server_ip = ""

  cluster_network_name = data.harvester_clusternetwork.mgmt.name
}
```
(**note:** this will create an image to use by downloading from ubuntu and build a mgmt-vlan1 vm network, you may want to adjust this as needed if there are other naming conflicts etc)
(**additional note:** opensuse leap images historically sometimes have problems, you may need to visit the [repository](https://download.opensuse.org/repositories/Cloud:/Images:/Leap_15.4/images/) to try to acquire the more-recent link for the NoCloud QCOW2 x86_64 based image, pagination is at the bottom of the page)

4. init and apply that terraform:
    - `terraform init` (while in directory of `harvester-setup`)
    - `terraform plan` (while in directory of `harvester-setup`)
    - `terraform apply` (while in directory of `harvester-setup`)

5. validate the scripts where able to create the network and grab an image to utilize for testing

### Rancher Setup
1. inside the `rancher-setup` folder, in the respective `provider.tf` file add:
```
terraform {
  required_providers {
    rancher2 = {
      source = "terraform.local/local/rancher2"
      version = "3.0.0-rc2"
    }
  }
}


provider "rancher2" {
  api_url    = "<>"
  access_key = "<>"
  secret_key = "<>"
  insecure = true
}

```
(**note:** the api_url, access_key, secret_key all reference the API key you created earlier in Rancher)

2. inside the `rancher-setup` folder, in the respective `main.tf` file add:
```

data "rancher2_cluster_v2" "foo-harvester" {
  name = "foo-harvester"
}

# Create a new Cloud Credential for an imported Harvester cluster
resource "rancher2_cloud_credential" "foo-harvester" {
  name = "foo-harvester"
  harvester_credential_config {
    cluster_id = data.rancher2_cluster_v2.foo-harvester.cluster_v1_id
    cluster_type = "imported"
    kubeconfig_content = data.rancher2_cluster_v2.foo-harvester.kube_config
  }
}

# Create a new rancher2 machine config v2 using harvester node_driver
resource "rancher2_machine_config_v2" "foo-harvester-v2" {
  generate_name = "foo-harvester-v2"
  harvester_config {
    vm_namespace = "default"
    cpu_count = "2"
    memory_size = "4"
    disk_info = <<EOF
    {
        "disks": [{
            "imageName": "harvester-public/opensuse-leap-15-4",
            "size": 40,
            "bootOrder": 1
        }]
    }
    EOF
    network_info = <<EOF
    {
        "interfaces": [{
            "networkName": "harvester-public/mgmt-vlan1"
        }]
    }
    EOF
    ssh_user = "opensuse"
    user_data = "I2Nsb3VkLWNvbmZpZwpwYWNrYWdlX3VwZGF0ZTogdHJ1ZQpwYWNrYWdlczoKICAtIHFlbXUtZ3Vlc3QtYWdlbnQKICAtIGlwdGFibGVzCnJ1bmNtZDoKICAtIC0gc3lzdGVtY3RsCiAgICAtIGVuYWJsZQogICAgLSAnLS1ub3cnCiAgICAtIHFlbXUtZ3Vlc3QtYWdlbnQuc2VydmljZQo="
  }
}

resource "rancher2_cluster_v2" "foo-harvester-v2" {
  name = "foo-harvester-v2"
  kubernetes_version = "v1.24.11+rke2r1"
  rke_config {
    machine_pools {
      name = "pool1"
      cloud_credential_secret_name = rancher2_cloud_credential.foo-harvester.id
      control_plane_role = true
      etcd_role = true
      worker_role = true
      quantity = 1
      machine_config {
        kind = rancher2_machine_config_v2.foo-harvester-v2.kind
        name = rancher2_machine_config_v2.foo-harvester-v2.name
      }
    }
    machine_selector_config {
      config = {
        cloud-provider-name = ""
      }
    }
    machine_global_config = <<EOF
cni: "calico"
disable-kube-proxy: false
etcd-expose-metrics: false
EOF
    upgrade_strategy {
      control_plane_concurrency = "10%"
      worker_concurrency = "10%"
    }
    etcd {
      snapshot_schedule_cron = "0 */5 * * *"
      snapshot_retention = 5
    }
    chart_values = ""
  }
}
```
(**note:** pay attention to change `name` for the `data` resource of the rancher2_cluster_v2 to your respective name that you gave your imported Harvester cluster in Rancher v2.7.X)

3. init and apply that terraform:
    - `terraform init` (while in directory of `harvester-setup`)
    - `terraform plan` (while in directory of `harvester-setup`)
    - `terraform apply` (while in directory of `harvester-setup`)


### Verify Steps:
1. Verify in Rancher that the RKE2 cluster is able to be provisioned and can be accessed
1. Verify that the `rancher2_cluster_v2` setup can be destroyed as well w/ `terraform destroy` inside the `rancher-setup` folder
1. Verify VM Affinity rules work:
- in your harvester cluster of N nodes on 1 of the nodes create labels on the host, cross-reference: [topology labels on harvester host](https://docs.harvesterhci.io/v1.1/rancher/node/node-driver/#sync-topology-labels-to-the-guest-cluster-node)
- then cultivate a JSON payload that looks something like:
```
{
  "nodeAffinity": {
    "requiredDuringSchedulingIgnoredDuringExecution": {
      "nodeSelectorTerms": [
        {
          "matchExpressions": [
            {
              "key": "topology.kubernetes.io/zone",
              "operator": "In",
              "values": [
                "us-fremont-1a"
              ]
            },
            {
              "key": "network.harvesterhci.io/mgmt",
              "operator": "In",
              "values": [
                "true"
              ]
            }
          ]
        }
      ]
    }
  }
}
```
(**note:** replace the `us-fremont-1a` for whatever zone value you provided as a topology label on the Host in your Harvester cluster)
- then base64 encode that JSON, and add it to the `main.tf` in `rancher-setup` folder's `resource "rancher2_machine_config_v2" "foo-harvester-v2"`, with the property of `vm_affinity` as documented [here](https://github.com/rancher/terraform-provider-rancher2/blob/v3.0.0/docs/resources/machine_config_v2.md)
- verify when terraform init, plan, apply, provisions the cluster, and that the cluster's VM on Harvester is running on the respective Harvester host with the labels