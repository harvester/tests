---
title: Test zero downtime for live migration ping test	
---
1. Continually ping VM
1. Verify that ping is getting a response
1. Live migrate VM to new host
1. Verify that ping continues

## Expected Results
1. Ping should get response
1. VM should start to migrate
1. Ping should not get any dropped packets