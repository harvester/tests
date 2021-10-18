---
title: Create a harvester cluster with different images	
---
1. d a harvester node template
1. Set the image, it should be a drop-down list, refer to "Test Data" for other values
    - ubuntu-18.04-server-cloudimg-amd64.img
    - focal-server-cloudimg-amd64-disk-kvm.img
1. Use this template to create the corresponding cluster

## Expected Results
1. The status of the created cluster shows active
1. The status of the corresponding vm on harvester active
1. The information displayed on rancher and harvester matches the template configuration
1. The drop-down list of images in the harvester node template corresponds to the list of images in the harvester