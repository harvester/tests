---
title: VM Import/Migration
---

* Related issues: [#2274](https://github.com/harvester/harvester/issues/2274) [Feature] VM Import/Migration

## Category: 
* Virtual Machine

## Test Information
Test Environment: 
* 1 node harvester on local kvm machine
* Harvester version: v1.1.0-rc1
* Vsphere: 7.0
* Openstack: Simulated using running devstack
* Download kubeconfig for harvester cluster

## Environment Setup

1. Prepare Harvester master node
2. Prepare vsphere setup (or use existing setup)
3. Prepare a devstack cluster (Openstack 16.2)


## Verification Steps

### Verify VmwareSource
* Define a secret for your vmware cluster

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
* Define a VmwareSource Object
```
apiVersion: migration.harvesterhci.io/v1beta1
kind: VmwareSource
metadata:
  name: vcsim
  namespace: default
spec:
  endpoint: "https://vscim/sdk"
  dc: "DCO"
  credentials:
    name: vsphere-credentials
    namespace: default
```

The controller will try and list VM's in the endpoint vmware cluster, and datacenter. If the details of credentials, endpoint and datacenter are correct, then the controller will mark the cluster as ready

```
$ kubectl get vmwaresource.migration 
NAME      STATUS
vcsim   clusterReady
```

### Verify OpenstackSource
* Define a secret for your Openstack cluster

```
apiVersion: v1
kind: Secret
metadata: 
  name: devstack-credentials
  namespace: default
stringData:
  "username": "user"
  "password": "password"
  "project_name": "admin"
  "domain_name": "default"
  "ca_cert": "pem-encoded-ca-cert"
```

* Define an OpenstackSource Object

```
apiVersion: migration.harvesterhci.io/v1beta1
kind: OpenstackSource
metadata:
  name: devstack
  namespace: default
spec:
  endpoint: "https://devstack/identity"
  region: "RegionOne"
  credentials:
    name: devstack-credentials
    namespace: default
```

The controller will try and list the VM's in the OpenstackSource project in the specified region, using the information from the credentials.

In this is successful the OpenstackSource will be marked as ready.

```
$ kubectl get openstacksource.migration
NAME       STATUS
devstack   clusterReady
```

### VirtualMachine Import using VmwareSource
* A VM import can be triggered by the creation of a VirtualMachineImport object as follows:

```
apiVersion: migration.harvesterhci.io/v1beta1
kind: VirtualMachineImport
metadata:
  name: alpine-export-test
  namespace: default
spec: 
  virtualMachineName: "alpine-export-test"
  networkMapping:
  - sourceNetwork: "dvSwitch 1"
    destinationNetwork: "default/vlan1"
  - sourceNetwork: "dvSwitch 2"
    destinationNetwork: "default/vlan2"
  sourceCluster: 
    name: vcsim
    namespace: default
    kind: VmwareSource
    apiVersion: migration.harvesterhci.io/v1beta1
```

The controller will check that the source is ready, before the virtualmachine import is initiated.

In case the VmwareSource is not ready, then the object will be requeued until the VmwareSource becomes ready

If the VmwareSource is ready, then the VirtualMachine identified by the `spec.virtualMachineName` will be powered off

The VirtualMachine will be exported as an ovf, the disks will be convered to raw images.

The raw images are exported via http endpoint for the vm-import-controller service and used to define a Harvester VirtualMachineImage. Each disk is imported as a VirtualMachineImage in harvester

Once VirtualMachineImages are "Active" in harvester, a PVC claim will be created for each VirtualMachineImage.

The new PVC Claim is used to create a kubevirt VirtualMachine.

As part of the VirtualMachine creation, the CPU, memory specs from the original VM are copied to create the new VM.

All network interfaces, including their mac addresses are copied into network interfaces to kubevirt VirtualMachine object.

If the VirtualMachine network interfaces source network matches the list of networks available in `spec.networkMapping` then the new network interface is attached to the destinationNetwork.

If there is no networkMapping defined, or no matching sourceNetwork is found then the network interface in the original VM is attached to the Harvester Management Network.

Once the VM object is created, the VirtualMachine is powered on, and the controller waits for the VirtualMachine to be `running`

### VirtualMachine Import using OpenstackSource
* A VM import can be triggered by the creation of a VirtualMachineImport object as follows:

```
apiVersion: migration.harvesterhci.io/v1beta1
kind: VirtualMachineImport
metadata:
  name: openstack-demo
  namespace: default
spec: 
  virtualMachineName: "openstack-demo" #Name or UUID for instance
  networkMapping:
  - sourceNetwork: "shared"
    destinationNetwork: "default/vlan1"
  - sourceNetwork: "public"
    destinationNetwork: "default/vlan2"
  sourceCluster: 
    name: devstack
    namespace: default
    kind: OpenstackSource
    apiVersion: migration.harvesterhci.io/v1beta1
```

The controller will check that the source is ready, before the virtualmachine import is initiated.

In case the VmwareSource is not ready, then the object will be requeued until the VmwareSource becomes ready

If the VmwareSource is ready, then the VirtualMachine identified by the `spec.virtualMachineName` will be powered off

The VirtualMachine will be exported as an ovf, the disks will be convered to raw images.

The raw images are exported via http endpoint for the vm-import-controller service and used to define a Harvester VirtualMachineImage. Each disk is imported as a VirtualMachineImage in harvester

Once VirtualMachineImages are "Active" in harvester, a PVC claim will be created for each VirtualMachineImage.

The new PVC Claim is used to create a kubevirt VirtualMachine.

As part of the VirtualMachine creation, the CPU, memory specs from the original VM are copied to create the new VM.

All network interfaces, including their mac addresses are copied into network interfaces to kubevirt VirtualMachine object.

If the VirtualMachine network interfaces source network matches the list of networks available in `spec.networkMapping` then the new network interface is attached to the destinationNetwork.

If there is no networkMapping defined, or no matching sourceNetwork is found then the network interface in the original VM is attached to the Harvester Management Network.

Once the VM object is created, the VirtualMachine is powered on, and the controller waits for the VirtualMachine to be `running`

### VirtualMachineImport states

When a VirtualMachineImport is completed the VirtualMachineImport job should be marked as `virtualMachineRunning`

```$ kubectl get virtualmachineimport.migration
NAME                    STATUS
alpine-export-test      virtualMachineRunning
openstack-cirros-test   virtualMachineRunning
```

* At this point the imported VirtualMachine is running in harvester and the `VirtualMachineImport` object can be removed if needed.

* In case of a failed import, deletion of the `VirtualMachineImport` object will gc any VirtualMachineImages created as part of the import process.

### Integration tests
Some core integrtion tests already exist with the `vm-import-controller` and are available under `tests/integration`

These test cases do however need access to a harvester, vmare and openstack cluster.

Users can run the vm-import-controller locally, with the following environment variables to trigger a VirtualMachineImports using VmwareSource and OpenstackSource

```
export GOVC_PASSWORD="vsphere-password"
export GOVC_USERNAME="vsphere-username"
export GOVC_URL="https://vcenter/sdk"
export GOVC_DATACENTER="vsphere-datacenter"
#The controller exposes the converted disks via a http endpoint and leverages the download capability of longhorn backing images
# the SVC address needs to be the address of node where integration tests are running and should be reachable from harvester cluster
export SVC_ADDRESS="address for node" 
export VM_NAME="vmware-export-test-vm-name"
export USE_EXISTING_CLUSTER=true
export OS_AUTH_URL="openstack/identity" #Keystone endpoint
export OS_PROJECT_NAME="openstack-project-name"
export OS_USER_DOMAIN_NAME="openstack-user-domain"
export OS_USERNAME="openstack-username"
export OS_PASSWORD="openstack-password"
export OS_VM_NAME="openstack-export-test-vm-name"
export OS_REGION_NAME="openstack-region"
export KUBECONFIG="kubeconfig-for-harvester-cluster"
```

## Expected Results
- VirtualMachines should be imported from Vmware / Openstack to Harvester cluster.
- Source VirtualMachines should be powered off

## Current limitations
- In rc1 the vm-import-controller is using ephemeral storage, which is allocated from /var/lib/kubelet. This may limit the size of VM's that can be imported.