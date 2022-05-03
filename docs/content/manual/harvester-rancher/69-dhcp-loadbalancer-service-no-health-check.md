---
title: 69-DHCP Harvester LoadBalancer service no health check 	
---
Prerequisite: 
Already provision RKE1/RKE2 cluster in previous test case

1. Open `Global Settings` in hamburger menu
1. Replace `ui-dashboard-index` to `https://releases.rancher.com/harvester-ui/dashboard/latest/index.html`
1. Change `ui-offline-preferred` to `Remote`
1. Refresh the current page (ctrl + r)
1. Open provisioned RKE2 cluster from hamburger menu
1. Drop down `Service Discovery`
1. Click `Services`
1. Click Create 
1. Select `Load Balancer`

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/f628094c-a195-4f99-9fb7-858d759dc019)

1. Given service name to make the load balancer name composed of the cluster name, namespace, svc name, and suffix(8 characters) more than 63 characters
1. Provide Listening port and Target port

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/2c20c759-4769-438b-94ad-5b995ba66873)

1. Click `Add-on Config`
1. Select Health Check port
1. Select `dhcp` as IPAM mode


1. Create another load balancer service with the name  characters.

## Expected Results
- Can create the load balance service correctly

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/4fbf9271-e3fa-4490-b1e9-8bb9c20060bf)

- Can operate and forward workload as expected
