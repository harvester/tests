---
title: Node Driver
---
To test the Harvester node driver. I'm using an external Rancher with docker on my laptop:
`docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:master-head`
`docker exec -ti <container_id> reset-password`