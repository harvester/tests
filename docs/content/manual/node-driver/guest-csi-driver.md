---
title: Guest CSI Driver
---
1. Start rancher using docker in a vm and start harvester in another
1. Import harvester into rancher from "Virtualization Management" page
1. On rancher, enable harvester node driver at "Cluster Management" -> "Drivers" -> "Node Driver"
1. Go back to "Cluster Management" and create a rke2 cluster using Harvester
1. Once the created cluster is active on the "Cluster Management" page, click on the "Explore"
1. Go to "Workload" -> "Deployment" and "Create" a new deployment, during which in the page of "Storage", click on "Add Volume" and select "Create Persistent Volume Claim" and select "Harvester" in the "Storage Class"
1. Click "Create" to create the deployment
1. Verify that on the Harvester side, a new volume is created.
1. Delete the created deployment and then delete the created pvc. Verify on the harvester side that the newly created volume is also deleted.
create another deployment, say nginx:latest with 8GB storage created as step 6.
1. "Execute shell" into the deployment above and use "dd" command to test the read & write speed in the directory where the pvc is mounted:
    - `dd if=/dev/zero of=tempfile bs=1M count=5120`
    - `dd if=/dev/null of=tempfile bs=1M count=5120`
1. SSH into a VM created on the bare metal and run the same `dd` command
    - `dd if=/dev/zero of=tempfile bs=1M count=5120`
    - `dd if=/dev/null of=tempfile bs=1M count=5120`
1. Scale down the above deployment to 0 replica and resize the pvc to 15GB on the harvester side:
1. Double check the pvc is resized on the longhorn side.

## Expected Results
1. The cluster should have similar storage speed performance
1. The PVC should resize and show it in the Longhorn UI