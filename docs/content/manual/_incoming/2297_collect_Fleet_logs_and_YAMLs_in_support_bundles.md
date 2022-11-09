---
title: collect Fleet logs and YAMLs in support bundles
category: UI
tag: dashboard, p2, functional
---
Ref: https://github.com/harvester/harvester/issues/2297


### Verify Steps:
1. Install Harvester with any nodes
1. Login to Dashboard then navigate to support page
1. Click **Generate Support Bundle** and do Generate
1. log files should be exist in the zipfile of support bundle:
    - `logs/cattle-fleet-local-system/fleet-agent-<randomID>/fleet-agent.log`
    - `logs/cattle-fleet-system/fleet-controller-<randomID>/fleet-controller.log`
    - `logs/cattle-fleet-system/gitjob-<randomID>/gitjob.log`

