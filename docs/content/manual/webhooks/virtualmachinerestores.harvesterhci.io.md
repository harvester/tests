---
title: virtualmachinerestores.harvesterhci.io
---
### GUI
1. Setup a backup target
1. Create a backup from a VM. Assume the VM name is vm-test
1. Wait until backup is done
1. Restore the backup to a VM, enter vm-test in the Virtual Machine Name field
### kube-api
```
$ cat restore.yaml 1
---
apiVersion: harvesterhci.io/v1beta1
kind: VirtualMachineRestore
metadata:
  name: restore-aaaa
  namespace: default
spec:
  newVM: false
  target:
    apiGroup: kubevirt.io
    kind: VirtualMachine
    name: ""
virtualMachineBackupName: test
$ kubectl create -f restore.yaml
```
## Expected Results
### GUI
1. The operation should fail with admission webhook "[validator.harvesterhci.io](http://validator.harvesterhci.io/)" denied the request: VM test is already exists
### kube-api
1. The operation should fail with:
`The request is invalid: spec.target.name: target VM name is empty`
