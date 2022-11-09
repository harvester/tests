---
title: VMIs created from VM Template don't have LiveMigrate evictionStrategy set
category: UI
tag: VM, p1, functional
---
Ref: https://github.com/harvester/harvester/issues/2357


### Verify Steps:
1. Install Harvester with at least 2 nodes
1. Create Image for VM Creation
1. Navigate to _Advanced/Templates_ and create a template `t1`
1. Create VM `vm1` from template `t1`
1. Edit YAML of `vm1`, field `spec.template.spec.evictionStrategy` should be `LiveMigrate`
1. Enable Maintenance Mode on the host which hosting `vm1`
1. `vm1` should start migrating automatically
1. Migration should success
