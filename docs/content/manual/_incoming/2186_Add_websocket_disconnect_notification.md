---
title: Add websocket disconnect notification
category: UI
tag: dashboard, p2, functional
---
Ref: https://github.com/harvester/harvester/issues/2186

![image](https://user-images.githubusercontent.com/5169694/177529443-a9478e33-a955-4b48-8485-ab6eabbf3824.png)


### Verify Steps:
1. Install Harvester with at least 2 nodes
1. Login to Dashboard via Node IP
1. Navigate to _Advanced/Settings_ and update **ui-index** to `https://releases.rancher.com/harvester-ui/dashboard/release-harvester-v1.0/index.html` and force refresh to make it applied.
1. restart the Node which holding the IP
1. Notification of websocket disconnected should appeared
