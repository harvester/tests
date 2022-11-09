---
title: enable/disable alertmanager on demand
category: UI
tag: dashboard, p1, integration
---
Ref: https://github.com/harvester/harvester/issues/2518

![image](https://user-images.githubusercontent.com/5169694/193554680-c2d6f7c0-5cf0-44ee-803e-c7abda408774.png)
![image](https://user-images.githubusercontent.com/5169694/193554761-1f28c3b9-8964-4bfa-8069-d5bcc7d8d837.png)


### Verify Steps:
1. Install Harvester with any nodes
1. Login to Dashboard, navigate to **Monitoring & Logging/Monitoring/Configuration** then select **Alertmanager** tab
1. Option Button `Enabled` should be checked
1. Select **Grafana** tab then access Grafana
1. Search _Alertmanager_ to access _Overview_ dashboard
1. Data should be available and keep updating
