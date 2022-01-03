---
title: Node Labeling for VM scheduling
---
Ref: https://github.com/harvester/harvester/issues/1416

## Verify Items
  - Host labels can be assigned during installation via config-create / config-join YAML.
  - Host labels can be managed post installation via the Harvester UI.
  - Host label information can be accessed in Rancher Virtualization Management UI.


## Case: Label node when installing
1. Install Harvester with config file and [**os.labels**](https://docs.harvesterhci.io/v1.0/install/harvester-configuration/#oslabels) option
2. Navigate to Host details then navigate to Labels in Config
3. Check additional labels should be displayed

## Case: Label node after installed
1. Install Harvester with at least 2 nodes
2. Navigate to Host details then navigate to **Labels** in Config
3. Use **edit config** to modify labels
5. Reboot the Node and wait until its state become active
6. Navigate to Host details then Navigate to Labels in Config
7. Check modified labels should be displayed

## Case: Node's Label availability
1. Install Harvester with at least 2 nodes
2. Navigate to Host details then navigate to **Labels** in Config
3. Use **edit config** to modify labels
5. Reboot the Node and wait until its state become active
6. Navigate to Host details then Navigate to Labels in Config
7. Check modified labels should be displayed
8. Install Rancher with any nodes
9. Navigate to _Virtualization Management_ and import former created Harvester
10. Wait Until state become **Active**
11. Click _Name_ field to visit dashboard
12. repeat step 2-7, and both compare from Harvester's dashboard (accessing via Harvester's VIP)
