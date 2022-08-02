---
title: 39-Standard user no Harvester Access
---
1. As admin import/register a harvester cluster in Rancher
1. As admin, Enable Harvester node driver
1. As a standard user User1, login to rancher
1. Verify User1 has no access to harvester cluster in Virtualization management page
1. Verify User1 can not create harvester cloud credential as User1
1. Verify User1 can not use this cloud credential to create a node template and can not use a node driver cluster 3 and can not CRUD each resource
