---
title: 30-Configure Harvester LoadBalancer service	
---
Prerequisite: 
Already provision RKE1/RKE2 cluster in previous test case

- Open `Global Settings` in hamburger menu
- Replace `ui-dashboard-index` to `https://releases.rancher.com/harvester-ui/dashboard/latest/index.html`
- Change `ui-offline-preferred` to `Remote`
- Refresh the current page (ctrl + r)
- Open provisioned RKE2 cluster from hamburger menu
- Drop down `Service Discovery`
- Click `Services`
- Click Create 
- Select `Load Balancer`

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/f628094c-a195-4f99-9fb7-858d759dc019)

- Given service name to make the load balancer name composed of the cluster name, namespace, svc name, and suffix(8 characters) more than 63 characters
- Provide Listening port and Target port

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/2c20c759-4769-438b-94ad-5b995ba66873)

- Click `Add-on Config`
- Select Health Check port
- Select `dhcp` as IPAM mode
- Provide Health Check Threshold
- Provide Health Check Failure Threshold
- Provide Health Check Period
- Provide Health Check Timeout
- Click Create button

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/a8d11df6-cc76-4897-8310-def670682775)

- Create another load balancer service with the name  characters.

## Expected Results
- Can create the load balance service correctly

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/4fbf9271-e3fa-4490-b1e9-8bb9c20060bf)

- Can operate and forward workload as expected
