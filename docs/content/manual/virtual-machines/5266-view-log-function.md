---
title: View log function on virtual machine
---

* Related issues: [#5266](https://github.com/harvester/harvester/issues/5266) [BUG] Click View Logs option on virtual machine dashboard can't display any log entry


## Category: 
* Virtual Machines

## Verification Steps
1. Create one virtual machines named `vm1` in the Harvester virtual machine page
1. Wait until the `vm1` in running state
1. Click the View Logs in the side option menu
1. Check the log panel content of vm
1. Click the `Clear` button
1. Click the `Download` button
1. Enter some query sting in the `Filter` field
1. Click settings, change the `Show the latest` to different options
1. Uncheck/Check the `Wrap Lines`
1. Uncheck/Check the `Show Timestamps`

## Expected Results
* Should display the detailed log entries on the vm log panel including timestamp and content
* All existing logs would be cleaned up 
* Ensure new logs will display on the panel
* Check can correctly download the log to the `.log` file and contain all the details
* Check the log entries contains the filter string can display correctly
* Check each different options of `Show the latest` log option can display log according to the settings
* Check the log entries can be wrapped or unwrapped 
* Check the log entries can display with/without timestamp
