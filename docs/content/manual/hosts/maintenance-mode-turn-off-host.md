---
title: Turn off host that is in maintenance mode	
---
1. Put host in maintenance mode
2. Migrate VMs
3. Wait for VMs to migrate
4. Wait for any vms to migrate off
5. Shut down Host

## Expected Results
1. Host should start to go into maintenance mode
2. Any VMs should migrate off
3. Host should go into maintenance mode
4. host should shut down
5. Maintenance mode label in hosts list should go red

### Known bugs
https://github.com/harvester/harvester/issues/1272
