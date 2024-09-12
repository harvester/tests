---
title: VM import with EFI mode and secure boot
---

* Related issues: [#5846](https://github.com/harvester/harvester/issues/5846) [ENHANCEMENT] vm-import-controller enhancements

## Category: 
* Virtual Machine

## OpenStack Prerequisite Setup
1. Prepare a baremetal or virtual machine to host the OpenStack service 
1. Or use the automated Jenkins pipeline to prepare a devstack cluster (Openstack 16.2) (stable/train)
1. Install OpenStack command line tool on your local machine (introduce in next section)

## VMware vSphere Prerequisite Setup
1. Get the available access to the existing or prepared vSphere client (v7.1)

## Harvester Prerequisite Setup
1. Harvester can connect to the OpenStack dashboard and API endpoint
1. Harvester can connect to the vSphere client dashboard and API endpoint
1. Enable the `vm-import-controller` in the `Addons` page
1. Create the `vlan1` vm network on the `mgmt` interface

## Install OpenStack command line tool
1. Require python 3.10 or you can use virtual environment (venv)
  ```
  virtualenv venv --python=python3.10
  source venv/bin/activate
  ```
1. Install OpenStack client 
  ```
  pip install python-openstackclient
  ```
1. Download the OpenStack cloud.yaml file 
   - Access the openstack dashboard
   - Open `API Access` page
   - Click the `Download OpenStack RC File` button
   - Select the `OpenStack cloud.yaml File`
1. Copy the cloud.yaml file to your openstack config folder 
  ```
  mkdir -p ~/.config/openstack
  cp -v ~/Documents/Harvester/Openstack/clouds.yaml ~/.config/openstack
  ```
1. Check can list the image list on OpenStack Server 
  ```
  openstack image list --os-auth-url <openstack URL>/identity --os-identity-api-version 3 --os-project-name admin --os-project-domain-name default --os-username <username> --os-password <password>

  ```


## VmwareSource Verification Steps

### Setup VmwareSource secret and object
* Access Harvester node and change to root
* Define and create a secret for your vmware cluster

  ```
  apiVersion: v1
  kind: Secret
  metadata: 
    name: vsphere-credentials
    namespace: default
  stringData:
    "username": "user"
    "password": "password"
  ```

* Define and create a VmwareSource Object

  ```
  apiVersion: migration.harvesterhci.io/v1beta1
  kind: VmwareSource
  metadata:
    name: vcsim
    namespace: default
  spec:
    endpoint: "<vSphere client URL>/sdk"
    dc: "Datacenter" 
    credentials:
      name: vsphere-credentials
      namespace: default
  ```

* Check the VMwareSource Cluster is Ready
  ```
  harvester-node-0:~ # kubectl get vmwaresource.migration
  NAME    STATUS
  vcsim   clusterReady
  ```

* If failed to connect to the VMwareSource object, check the following
  - Use IP address instead of dns name (Use nslookup command)
  - Check the datacenter value
  - Check the username and password

### Verify WMware EFI Based VM with secure boot migration
1. Access the vSphere Client 
1. Right Click on the Cluster compute source -> New Virtual Machine
1. You can create a new virtual machine or clone an existing one
1. Select an available storage
1. Finish the rest option
1. After VM created, edit the settings 
1. Select VM Options and expand Boot Options
1. Select Firmware to `EFI(recommended)`
1. Select `Secure Boot` option
{{< image "images/addons/5846-vmware-uefi-secure-vm.png" >}}
1. Save and ensure VM start in running state
1. Access to Harvester node and change to root
1. Create the yaml file content for the VMware VirtualMachineImport object 
  ```
  apiVersion: migration.harvesterhci.io/v1beta1
  kind: VirtualMachineImport
  metadata:
    name: vcsim-uefi-sec
    namespace: default
  spec:
    virtualMachineName: "dl-opensuse-uefi-secure"
    networkMapping:
    - sourceNetwork: VM Network
      destinationNetwork: "default/vlan1"
    sourceCluster:
      name: vcsim
      namespace: default
      kind: VmwareSource
      apiVersion: migration.harvesterhci.io/v1beta1
  ```
1. Wait for the vm-import-controller to start image transfer and create virtual machine

### Expected Result
1. Can import UEFI mode with secure boot VM from VMware to Harvester
1. The imported VM started in running state
1. Check the config of imported VM
1. In the `Advanced Options` page, check `Booting in EFI mode` and `Secure Boot` are both selected 
{{< image "images/addons/5846-harvester-uefi-secure-vm.png" >}}


### Verify WMware EFI Based VM migration
1. Access the vSphere Client 
1. Right Click on the Cluster compute source -> New Virtual Machine
1. You can create a new virtual machine or clone an existing one
1. Select an available storage
1. Finish the rest option
1. After VM created, edit the settings 
1. Select VM Options and expand Boot Options
1. Select Firmware to `EFI(recommended)`
{{< image "images/addons/5846-vmware-uefi-vm.png" >}}
1. Save and ensure VM start in running state
1. Access to Harvester node and change to root
1. Create the yaml file content for the VMware VirtualMachineImport object 
  ```
  apiVersion: migration.harvesterhci.io/v1beta1
  kind: VirtualMachineImport
  metadata:
    name: vcsim-uefi
    namespace: default
  spec:
    virtualMachineName: "dl-opensue-uefi"
    networkMapping:
    - sourceNetwork: VM Network
      destinationNetwork: "default/vlan1"
    sourceCluster:
      name: vcsim
      namespace: default
      kind: VmwareSource
      apiVersion: migration.harvesterhci.io/v1beta1
  ```

1. Wait for the vm-import-controller to start image transfer and create virtual machine

### Expected Result
1. Can import UEFI mode VM from VMware to Harvester
1. The imported VM started in running state
1. Check the config of imported VM
1. In the `Advanced Options` page, check only the `Booting in EFI mode` be selected 
{{< image "images/addons/5846-harvester-uefi-vm.png" >}}



### Verify VMware BIOS based VM migration
1. Access the vSphere Client 
1. Right Click on the Cluster compute source -> New Virtual Machine
1. You can create a new virtual machine or clone an existing one
1. Select an available storage
1. Finish the rest option
1. After VM created, edit the settings 
1. Select VM Options and expand Boot Options
1. Select Firmware to `BIOS(recommended)`
{{< image "images/addons/5846-vmware-bios-vm.png" >}}
1. Save and ensure VM start in running state
1. Access to Harvester node and change to root
1. Create the yaml file content for the VMware VirtualMachineImport object 
  ```
  apiVersion: migration.harvesterhci.io/v1beta1
  kind: VirtualMachineImport
  metadata:
    name: vcsim-bios
    namespace: default
  spec:
    virtualMachineName: "dl-ubuntu-bios"
    networkMapping:
    - sourceNetwork: VM Network
      destinationNetwork: "default/vlan1"
    sourceCluster:
      name: vcsim
      namespace: default
      kind: VmwareSource
      apiVersion: migration.harvesterhci.io/v1beta1
  ```

1. Wait for the vm-import-controller to start image transfer and create virtual machine

### Expected Result
1. Can import BIOS mode VM from VMware to Harvester
1. The imported VM started in running state
1. Check the config of imported VM
1. In the `Advanced Options` page, check only the `Booting in EFI mode` is `not selected`  
{{< image "images/addons/5846-harvester-bios-vm.png" >}}


### Verify WMware EFI based VM migration using a custom storage class 
1. Access to Harvester dashboard
1. Open the Storage Classes page
1. Create a new storage class named `single-replica`
1. Given "Number Of Replicas" value to `1`
1. Access the vSphere Client 
1. Right Click on the Cluster compute source -> New Virtual Machine
1. You can create a new virtual machine or clone an existing one
1. Select an available storage
1. Finish the rest option
1. After VM created, edit the settings 
1. Select VM Options and expand Boot Options
1. Select Firmware to `EFI(recommended)`
1. Save and ensure VM start in running state
1. Access to Harvester node and change to root
1. Create the yaml file content for the VMware VirtualMachineImport object
1. Given the storageClass value to `single-replica`
  ```
  apiVersion: migration.harvesterhci.io/v1beta1
  kind: VirtualMachineImport
  metadata:
    name: vmw-uefi-storage
    namespace: default
  spec:
    virtualMachineName: "dl-uefi-storage"
    storageClass: single-replica
    networkMapping:
    - sourceNetwork: VM Network
      destinationNetwork: "default/vlan1"
    sourceCluster:
      name: vcsim
      namespace: default
      kind: VmwareSource
      apiVersion: migration.harvesterhci.io/v1beta1
  ```
1. Wait for the vm-import-controller to start image transfer and create virtual machine

### Expected Result
1. Can import EFI mode VM from VMware to Harvester
1. The imported VM started in running state
1. Check the imported VM `image` use the specific `single replica` storage class
{{< image "images/addons/5846-harvester-image-storage-class.png" >}}
1. Check the imported VM `volume` use the specific "single replica" storage class
{{< image "images/addons/5846-harvester-volume-storage-class.png" >}}

## OpenstackSource Verification Steps

### Verify OpenStack EFI Based VM with secure boot migration
1. Access the OpenStack dashboard
1. Open images page -> Create image
1. Upload a brand new image from `Image Source` and select the `Format`
1. Wait for the image upload complete
1. Use OpenStack CLI tool to check all available image list
  ```
  openstack image list --os-auth-url <openstack dashboard url>/identity --os-identity-api-version 3 --os-project-name admin --os-project-domain-name default --os-username <username> --os-password <password>

  ```
1. You can find all available image list with ID 
  ```
  +--------------------------------------+--------------------------+--------+
  | ID                                   | Name                     | Status |
  +--------------------------------------+--------------------------+--------+
  | 9ba4963e-f412-409d-81a7-05ce6ae39301 | cirros-0.4.0-x86_64-disk | active |
  | fa3ab60f-32b0-4f69-aba3-e35a9970b096 | openSUSE-Leap-15.4       | active |
  | 702b597f-dc2a-4f5e-b879-e7ae99642978 | ubuntu-focal-20.04       | active |
  +--------------------------------------+--------------------------+--------+
  ```
1. Select the image ID that you want it to become `UEFI mode` and `Secure boot` 
1. Use OpenStack CLI tool to set the image to required boot options and machine type
  ```
  openstack image set --property hw_firmware_type=uefi --property os_secure_boot=required fa3ab60f-32b0-4f69-aba3-e35a9970b096 --os-auth-url <openstack dashboard URL>/identity --os-identity-api-version 3 --os-project-name admin --os-project-domain-name default --os-username <username> --os-password <password>
  ```
1. Back to the OpenStack dashboard
1. Open the Images page, select the image you set with openstack CLI and click `Launch`
1. Given the `Instance name`, `Flavor` and `Network` to create a new vm
1. Ensure the VM is running well on the OpenStack Instance page

1. Access to Harvester node and change to root
1. Create the yaml file content for the OpenStack VirtualMachineImport object 
  ```
  apiVersion: migration.harvesterhci.io/v1beta1
  kind: VirtualMachineImport
  metadata:
    name: uefi-secure
    namespace: default
  spec:
    virtualMachineName: "<instance name>" #Name or UUID for instance
    networkMapping:
    - sourceNetwork: "external"
      destinationNetwork: "default/vlan1"
    sourceCluster:
      name: microstack
      namespace: default
      kind: OpenstackSource
      apiVersion: migration.harvesterhci.io/v1beta1
  ```
1. Wait for the vm-import-controller to start image transfer and create virtual machine

### Expected Result
1. Can import UEFI mode with secure boot VM from VMware to Harvester
1. The imported VM started in running state
1. Check the config of imported VM
1. In the `Advanced Options` page, check `Booting in EFI mode` and `Secure Boot` are both selected 
{{< image "images/addons/5846-harvester-uefi-secure-vm.png" >}}



### Verify OpenStack EFI Based VM migration
1. Access the OpenStack dashboard
1. Open images page -> Create image
1. Upload a brand new image from `Image Source` and select the `Format`
1. Wait for the image upload complete
1. Use OpenStack CLI tool to check all available image list
  ```
  openstack image list --os-auth-url <openstack dashboard url>/identity --os-identity-api-version 3 --os-project-name admin --os-project-domain-name default --os-username <username> --os-password <password>

  ```
1. You can find all available image list with ID 
1. Select the image ID that you want it to become `UEFI mode` only 
1. Use OpenStack CLI tool to set the image to required boot options and machine type
  ```
  openstack image set --property hw_firmware_type=uefi <image-id> --os-auth-url <openstack url>/identity --os-identity-api-version 3 --os-project-name admin --os-project-domain-name default --os-username <username> --os-password <password>
  ```
1. Back to the OpenStack dashboard
1. Open the Images page, select the image you set with openstack CLI and click `Launch`
1. Given the `Instance name`, `Flavor` and `Network` to create a new vm
1. Ensure the VM is running well on the OpenStack Instance page

1. Access to Harvester node and change to root
1. Create the yaml file content for the OpenStack VirtualMachineImport object 
  ```
  apiVersion: migration.harvesterhci.io/v1beta1
  kind: VirtualMachineImport
  metadata:
    name: uefi
    namespace: default
  spec:
    virtualMachineName: "<instance name>" #Name or UUID for instance
    networkMapping:
    - sourceNetwork: "external"
      destinationNetwork: "default/vlan1"
    sourceCluster:
      name: microstack
      namespace: default
      kind: OpenstackSource
      apiVersion: migration.harvesterhci.io/v1beta1
  ```
1. Wait for the vm-import-controller to start image transfer and create virtual machine

### Expected Result
1. Can import UEFI mode VM from VMware to Harvester
1. The imported VM started in running state
1. Check the config of imported VM
1. In the `Advanced Options` page, check only the `Booting in EFI mode` be selected 
{{< image "images/addons/5846-harvester-uefi-vm.png" >}}


### Verify OpenStack BIOS based VM migration
1. Access the OpenStack dashboard
1. Open images page -> Create image
1. Upload a brand new image from `Image Source` and select the `Format`
1. Wait for the image upload complete
1. The default image boot mode is BIOS type, we don't need to run the openstack CLI tool
1. Back to the OpenStack dashboard
1. Open the Images page, select the image you set with openstack CLI and click `Launch`
1. Given the `Instance name`, `Flavor` and `Network` to create a new vm
1. Ensure the VM is running well on the OpenStack Instance page

1. Access to Harvester node and change to root
1. Create the yaml file content for the OpenStack VirtualMachineImport object 
  ```
  apiVersion: migration.harvesterhci.io/v1beta1
  kind: VirtualMachineImport
  metadata:
    name: bios
    namespace: default
  spec:
    virtualMachineName: "<instance name>" #Name or UUID for instance
    networkMapping:
    - sourceNetwork: "external"
      destinationNetwork: "default/vlan1"
    sourceCluster:
      name: microstack
      namespace: default
      kind: OpenstackSource
      apiVersion: migration.harvesterhci.io/v1beta1
  ```
1. Wait for the vm-import-controller to start image transfer and create virtual machine

### Expected Result
1. Can import BIOS mode VM from VMware to Harvester
1. The imported VM started in running state
1. Check the config of imported VM
1. In the `Advanced Options` page, check only the `Booting in EFI mode` is `not selected`  
{{< image "images/addons/5846-harvester-bios-vm.png" >}}


### Verify Openstack EFI based VM migration using a custom storage class 
1. Access to Harvester dashboard
1. Open the Storage Classes page
1. Create a new storage class named `single-replica`
1. Given "Number Of Replicas" value to `1`
1. We can use the existing `EFI mode` OpenStack VM created before 
1. Access to Harvester node and change to root
1. Create the yaml file content for the VMware VirtualMachineImport object
1. Given the storageClass value to `single-replica`
  ```
  apiVersion: migration.harvesterhci.io/v1beta1
  kind: VirtualMachineImport
  metadata:
    name: uefi-storage-class-test
    namespace: default
  spec:
    virtualMachineName: "<instance name>" #Name or UUID for instance
    storageClass: single-replica
    networkMapping:
    - sourceNetwork: "external"
      destinationNetwork: "default/vlan1"
    sourceCluster:
      name: microstack
      namespace: default
      kind: OpenstackSource
      apiVersion: migration.harvesterhci.io/v1beta1
  ```

1. Wait for the vm-import-controller to start image transfer and create virtual machine

### Expected Result
1. Can import EFI mode VM from VMware to Harvester
1. The imported VM started in running state
1. Check the imported VM `image` use the specific `single replica` storage class
{{< image "images/addons/5846-harvester-image-storage-class.png" >}}
1. Check the imported VM `volume` use the specific "single replica" storage class
{{< image "images/addons/5846-harvester-volume-storage-class.png" >}}