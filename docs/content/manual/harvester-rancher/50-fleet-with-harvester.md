---
title: 50-Use fleet when a harvester cluster is imported to rancher
---

1. deploy rancher with harvester enabled
1. docker: --features=harvester=enabled
1. helm: --set 'extraEnv[0].name=CATTLE_FEATURES' --set 'extraEnv[0].value=harvester=enabled
1. import a harvester setup
1. go to fleet → repos -> create
1. validate that that the harvester cluster is NOT in the dropdown for cluster deployments
1. validate that selecting the 'all clusters' option for deployment does NOT deploy to the harvester cluster