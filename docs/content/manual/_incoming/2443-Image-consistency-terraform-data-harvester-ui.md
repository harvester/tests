---
title: Image handling consistency between terraform data resource and Harvester UI created image
---

* Related issues: [#2443](https://github.com/harvester/harvester/issues/2443) [BUG] Image handling inconsistency between "Harvester Terraform harvester_image data source" vs. "UI created Image"
  
## Category: 
* Terraform

## Verification Steps
1. Download latest terraform-provider [terraform-provider-harvester_0.5.1_linux_amd64.zip](https://github.com/harvester/terraform-provider-harvester/releases/download/v0.5.1/terraform-provider-harvester_0.5.1_linux_amd64.zip)
1. Extra the zip file
1. Create the install-terraform-provider-harvester.sh with the following content
    ```
    #!/usr/bin/env bash
    [[ -n $DEBUG ]] && set -x
    set -eou pipefail

    usage() {
        cat <<HELP
    USAGE:
        install-terraform-provider-harvester.sh
    HELP
    }

    version=0.5.1
    arch=linux_amd64
    terraform_harvester_provider_bin=./terraform-provider-harvester

    terraform_harvester_provider_dir="${HOME}/.terraform.d/plugins/registry.terraform.io/harvester/harvester/${version}/${arch}/"
    mkdir -p "${terraform_harvester_provider_dir}"
    cp ${terraform_harvester_provider_bin} "${terraform_harvester_provider_dir}/terraform-provider-harvester_v${version}"
    ```
1. Rename the extraced `terraform-provider-harvester_v0.5.1` to `terraform-provider-harvester` in the same folder with the install script
1. Execute the installation script 
1. Clone the terraform-provider project 
1. Get the Harvester kubeconfig and place to the specific config file 
1. Specify the kubeconfig path in `provider.tf`
    ```
    terraform {
        required_version = ">= 0.13"
        required_providers {
        harvester = {
            source  = "harvester/harvester"
            version = "0.5.1"
        }
        }
    }
    
    provider "harvester" {
        kubeconfig = "/home/davidtclin/.kube/config"
    }
    ```  
1. Create a image ubuntu-18.04-minimal-cloudimg-amd64.img in the namespace harvester-public form UI side
1. Create a data source harvester_image.ubuntu1804 in resource.tf 
    ```
    data "harvester_image" "ubuntu1804" {
    namespace    = "harvester-public"
    display_name = "ubuntu-18.04-minimal-cloudimg-amd64.img"
    }
    ```
1. Execute `terraform init -upgrade`
1. Execute `terraform apply`
1. Execute `terraform show`
    ```
    ...
    ...
    Plan: 1 to add, 0 to change, 0 to destroy.

    Do you want to perform these actions?
    Terraform will perform the actions described above.
    Only 'yes' will be accepted to approve.

    Enter a value: yes

    harvester_ssh_key.davidtclin: Creating...
    harvester_ssh_key.davidtclin: Creation complete after 0s [id=default/davidtclin]

    Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
    ```

1. Execute `terraform show`
    ```
    davidtclin@localhost:~/Documents/Harvester/workspace/terraform-provider-harvester/examples/test> terraform show
    # data.harvester_image.ubuntu1804:
    data "harvester_image" "ubuntu1804" {
        display_name       = "ubuntu-18.04-minimal-cloudimg-amd64.img"
        id                 = "harvester-public/image-7w8tp"
        name               = "image-7w8tp"
        namespace          = "harvester-public"
        progress           = 100
        size               = 202637312
        source_type        = "download"
        state              = "Active"
        storage_class_name = "longhorn-image-7w8tp"
        tags               = {}
        url                = "https://cloud-images.ubuntu.com/minimal/releases/bionic/release/ubuntu-18.04-minimal-cloudimg-amd64.img"
    }
    ...
    ```


## Expected Results
We can use the data source refer to the display name that had been used via creation of the image via UI.

1. Image resource created in image UI
![image](https://user-images.githubusercontent.com/29251855/185184768-18708aaf-96a4-40c2-8d8f-247a21d42705.png)

1. Image state of running `terraform show`
    ```
    davidtclin@localhost:~/Documents/Harvester/workspace/terraform-provider-harvester/examples/test> terraform show
    # data.harvester_image.ubuntu1804:
    data "harvester_image" "ubuntu1804" {
        display_name       = "ubuntu-18.04-minimal-cloudimg-amd64.img"
        id                 = "harvester-public/image-7w8tp"
        name               = "image-7w8tp"
        namespace          = "harvester-public"
        progress           = 100
        size               = 202637312
        source_type        = "download"
        state              = "Active"
        storage_class_name = "longhorn-image-7w8tp"
        tags               = {}
        url                = "https://cloud-images.ubuntu.com/minimal/releases/bionic/release/ubuntu-18.04-minimal-cloudimg-amd64.img"
    }
    ...
    ```