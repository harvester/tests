---
title: Test zero downtime for live migration download test	
---
1. Connect to VM via console
1. Start a large file download
1. Live migrate VM to new host
1. Verify that file download does not fail

## Expected Results
1. Console should open
1. VM should start to migrate
1. File download should