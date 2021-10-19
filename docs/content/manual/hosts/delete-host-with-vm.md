---
title: Delete host that has VMs on it	
---
1. Navigate to the Hosts page and select the node
2. Click Delete

## Expected Results
1. An alert message should appear.
2. If VM exists it should stop user to delete the node or move VM to other node.
3. If VM is getting moved to another node and there is no space, it should stop user to delete the node.

### Existing bugs
https://github.com/harvester/harvester/issues/1004
