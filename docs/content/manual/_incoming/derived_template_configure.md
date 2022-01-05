---
title: Volume size should be editable on derived template
---
Ref: https://github.com/harvester/harvester/issues/1711

## Verify Items
  - Volume size can be changed when creating a derived template

## Case: Update volume size on new template derived from exist template
1. Install Harvester with any Nodes
2. Login to Dashboard
2. Create Image for Template Creation
3. Create Template `T1` with _Image Volume_ and additional _Volume_
4. Modify Template `T1` with update _Volume_ size
5. Volume size should be editable
6. Click Save, then edit new version of `T1`
7. Volume size should be updated as expected
