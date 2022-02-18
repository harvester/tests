---
title: Install 2 node Harvester with a Harvester token with multiple words
---

* Related issues: [#812](https://github.com/harvester/harvester/issues/812) ISO install accepts multiple words for 'cluster token' value resulting in failure to join cluster

## Verification Steps

1. Start Harvester install from ISO
1. At the 'Cluster token' prompt, enter, `here are words`
1. Proceed to complete the installation
1. Boot a secondary host from the installation ISO and select the option to join an existing cluster
1. At the 'Cluster token' prompt, enter, `here are words`
1. Proceed to complete the installation
1. Verify both hosts show in hosts list at VIP

## Expected Results
1. Install should complete successfully
1. Host should add with no errors
1. Both hosts should show up