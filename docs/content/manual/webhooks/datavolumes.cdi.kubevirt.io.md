---
title: datavolumes.cdi.kubevirt.io
---
## GUI
1. Create a VM in GUI and wait until it's running. Assume its name is test.
### kube-api
1. Try to delete its datavolume:
```
$ kubectl get vms
NAME AGE   STATUS  READY
test 5m16s Running True
```
1. There should be an datavolume bound to that VM
```
$ kubectl get dvs
NAME              PHASE     PROGRESS RESTARTS AGE
test-disk-0-klrft Succeeded 100.0%            5m18s
```
1. The user should not be able to delete the datavolume
```
$ kubectl delete dv test-disk-0-klrft The request is invalid: : can not delete the volume test-disk-0-klrft which is currently attached to VMs: default/test
``

## Expected Results
### kube-api
The deletion of its datavolume should fail.
