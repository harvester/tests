---
title: virtualmachinetemplateversions.harvesterhci.io
---
### kube-api
1. List default templates:
`$ kubectl get virtualmachinetemplateversions.harvesterhci.io -n harvester-public`
### GUI
1. Go to Advanced -> Templates page
1. Create a new template and set it as the default version
1. Try to delete the default version

## Expected Results
### kube-api
1. Default templates should exist:
```
NAME                             TEMPLATE_ID   VERSION   AGE
iso-image-base-version                         1         39m
raw-image-base-version                         1         39m
windows-iso-image-base-version                 1         39m
```
### GUI
1. Creating a new template should succeed
1. Deleting the default version of a template should fail with:
admission webhook "[validator.harvesterhci.io](http://validator.harvesterhci.io/)" denied the request: Cannot delete the default templateVersion.
