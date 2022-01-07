---
title: toggle harvester node driver with the harvester global flag
---

 * Related issue: [#1465](https://github.com/harvester/harvester/issues/1465) toggle harvester node driver with the harvester global flag

## Category: 
* Rancher Integration

## Environment setup
1. Install rancher `2.6.3` by docker
```
docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:v2.6.3
```


## Verification Steps
1. Environment preparation as above steps
1. Open global setting -> feature flag in rancher
1. Check harvester feature flag 
1. Open cluster management -> Driver page
1. Check harvester node driver
1. Deactivate harvester feature flag
1. Activate harvester feature flag
1. Deactivate harvester node driver
1. Activate harvester node driver 
1. Deactivate both harvester flag and node driver
1. Activate harvester feature flag 

## Expected Results
1. Harvester feature flag will be enabled by default and turned on harvester node driver accordingly
![image](https://user-images.githubusercontent.com/29251855/142818784-21d084eb-ed8e-4f7c-93a7-e224119c0190.png)

![image](https://user-images.githubusercontent.com/29251855/142818649-8bb1c585-f9dd-47fd-a8a2-80558f59fafd.png)

1. If the feature flag was turned off, nothing will change to the Harvester node driver.
![image](https://user-images.githubusercontent.com/29251855/142819289-6e06b72f-6631-44f1-83e1-77947dc4ba6d.png)

![image](https://user-images.githubusercontent.com/29251855/142819219-0f3a4eaf-f837-49cf-bdc7-347ff38c7a88.png)

1. Enable/disable the Harvester node driver will not affect the state of the feature flag.
![image](https://user-images.githubusercontent.com/29251855/142819526-321e2ead-474c-403a-88e6-14445f316c6c.png)

![image](https://user-images.githubusercontent.com/29251855/142819705-347aab30-cd92-4b45-935f-a3f0dcd17342.png)


1. If the feature flag was turned on, we enable the Harvester node driver automatically 
![image](https://user-images.githubusercontent.com/29251855/142819920-3b29e61a-7543-44e0-830c-4c450a1b30fa.png)