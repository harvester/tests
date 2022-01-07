---
title: Volume size should be editable on derived template
---
Ref: https://github.com/harvester/harvester/issues/1711

## Verify Items
  - Volume size can be changed when creating a derived template

## Case: Update volume size on new template derived from exist template
1. Install Harvester with any Nodes
1. Login to Dashboard
1. Create Image for Template Creation
1. Create Template `T1` with _Image Volume_ and additional _Volume_
1. Modify Template `T1` with update _Volume_ size
1. Volume size should be editable
1. Click Save, then edit new version of `T1`
1. Volume size should be updated as expected
