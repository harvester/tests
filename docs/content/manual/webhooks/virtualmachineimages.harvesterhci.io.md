---
title: virtualmachineimages.harvesterhci.io
---
### GUI
1. Create an image from GUI
1. Create another image with the same name. The operation should fail with admission webhook "[validator.harvesterhci.io](http://validator.harvesterhci.io/)" denied the request: A resource with the same name exists
### kube-api
1. Create an image from the manifest:
```
$ cat image.yaml
---
apiVersion: harvesterhci.io/v1beta1
kind: VirtualMachineImage
metadata:
  generateName: image-
  namespace: default
spec:
  sourceType: download
  displayName: cirros-0.5.1-x86_64-disk2.img
  url: http://192.168.2.106/cirros-0.5.1-x86_64-disk.img

$ kubectl create -f image.yml
virtualmachineimage.harvesterhci.io/image-8dkbq created
```
1. Try to create an image with the same manifest:
```
$ kubectl create -f image.yaml Error from server (Conflict): error when creating "image.yaml": admission webhook "validator.harvest
```
## Expected Results
### GUI
1. The operation should fail with admission webhook [validator.harvesterhci.io](http://validator.harvesterhci.io/) denied the request: A resource with the same name exists
### kube-api
1. Creating an image with the same manifest should fail.
