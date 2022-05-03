---
title: 70-Pool LoadBalancer service no health check
---
Prerequisite: 
Already provision RKE1/RKE2 cluster in previous test case

1. Open `Global Settings` in hamburger menu
1. Replace `ui-dashboard-index` to `https://releases.rancher.com/harvester-ui/dashboard/latest/index.html`
1. Change `ui-offline-preferred` to `Remote`
1. Refresh the current page (ctrl + r)
1. Access Harvester dashboard UI
1. Go to Settings
1. Create a vip-pool in Harvester settings.
  ![image](https://user-images.githubusercontent.com/29251855/158514040-bfcd9ff3-964a-4511-94d7-a497ef88848f.png)
1. Open provisioned RKE2 cluster from hamburger menu
1. Drop down `Service Discovery`
1. Click `Services`
1. Click Create 
1. Select `Load Balancer`
![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/f628094c-a195-4f99-9fb7-858d759dc019)

1. Given service name
1. Provide Listening port and Target port
  ![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/2c20c759-4769-438b-94ad-5b995ba66873)

1. Click `Add-on Config`
1. Provide Health Check port
1. Select `pool` as IPAM mode

## Expected Results
1. Can create load balance service correctly
1. Can operate and route to deployed service correctly