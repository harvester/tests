---
title: Support multiple VLAN physical interfaces
---

* Related issues: [#2259](https://github.com/harvester/harvester/issues/2259) [FEATURE] Support multiple VLAN physical interfaces
  
## Category: 
* Network

## Verification Steps
1. Create cluster network `cn1`
  ![image](https://user-images.githubusercontent.com/29251855/196580297-57541544-48f5-4492-b3e9-a3450697f490.png)

1. Create a vlanconfig `config-n1` on `cn1` which applied to node 1 only
  ![image](https://user-images.githubusercontent.com/29251855/196580491-0572c539-5828-4f2e-a0a6-59b40fcc549b.png)

1. Select an available NIC on the Uplink 
  ![image](https://user-images.githubusercontent.com/29251855/196580574-d38d59de-251c-4cf8-885d-655b76a78659.png)

1. Create a vlan, the cluster network `cn1` vlanconfig and provide valid vlan id `91`
  ![image](https://user-images.githubusercontent.com/29251855/196584602-b663ca69-da9a-42e3-94e0-41e094ff1d0b.png)

1. Create cluster network `cn2`
  ![image](https://user-images.githubusercontent.com/29251855/196580818-2ad7ed6b-db07-45e1-bb68-675f15b3fcf3.png)

1. Create a vlanconfig `config-n2` on `cn2` which applied to node 2 only
  ![image](https://user-images.githubusercontent.com/29251855/196583186-566af433-a37e-4d19-a660-879ce8e7f020.png)

1. Select an available NIC on the Uplink 
  ![image](https://user-images.githubusercontent.com/29251855/196584299-ba819310-8242-4196-a4d8-bacc7912c41d.png)
  ![image](https://user-images.githubusercontent.com/29251855/196584334-2b5ceaf1-3345-4cba-aaac-917dee70099f.png)

1. Create a vlan, the cluster network `cn2` vlanconfig and provide valid vlan id `92`
  ![image](https://user-images.githubusercontent.com/29251855/196585018-62bc4313-51c8-49e3-b9f7-c8c06564192e.png)
  ![image](https://user-images.githubusercontent.com/29251855/196586570-b57d1e1b-9db6-4b53-8e7c-80b9e35de788.png)
  ![image](https://user-images.githubusercontent.com/29251855/196586678-8d1c16db-f9a7-4dcc-9122-c43e0f259e48.png)

1. Create cluster network `cn3`
  ![image](https://user-images.githubusercontent.com/29251855/196586958-115c47ab-adc9-4873-831f-10704c148700.png)

1. Create a vlanconfig `config-n3` on `cn3` which applied to node 3 only
  ![image](https://user-images.githubusercontent.com/29251855/196587295-c6d46474-f58a-48dc-a2f7-42b5f6ed27cb.png)

1. Select an available NIC on the Uplink 
  ![image](https://user-images.githubusercontent.com/29251855/196588180-fb23fc8a-7c8d-48c7-bb1d-6fad72455ddd.png)

1. Create a vlan, select the cluster network `cn3` vlanconfig and provide valid vlan id `93`
  ![image](https://user-images.githubusercontent.com/29251855/196588462-d121008c-3afc-4f36-8ce5-f6bc2cc1ada8.png)
  ![image](https://user-images.githubusercontent.com/29251855/196589014-f00bc352-4b0c-45ee-9a20-c91d7ac54844.png)

1. Create a VM, use the vlan id `1` and specific at any node 
  ![image](https://user-images.githubusercontent.com/29251855/196592942-50f1b75a-61a1-4c09-8cbe-04956cf28ad5.png)

1. Create a VM, use the vlan id `91` and specified at `node1`
  ![image](https://user-images.githubusercontent.com/29251855/196591991-327bd314-ba61-491f-8e30-271b805b793f.png)

1. Create another VM, use the vlan id `92` 
  ![image](https://user-images.githubusercontent.com/29251855/196593067-08e3e64b-5421-4bf9-8cb7-496ee081122c.png)


## Expected Results
1. Can create different vlan on each cluster network
  ![image](https://user-images.githubusercontent.com/29251855/196589014-f00bc352-4b0c-45ee-9a20-c91d7ac54844.png)

1. Can create VM using vlan id `91` and retrieve IP address correctly
![image](https://user-images.githubusercontent.com/29251855/196592572-5f9f3b79-9c41-4714-9c88-821ac41f923d.png)

1. Can create VM using vlan id `92` and retrieve IP address correctly
![image](https://user-images.githubusercontent.com/29251855/196592853-1d092799-23ae-411c-97ee-163c88195c14.png)

1. Can create VM using vlan id `1` and retrieve IP address correctly
![image](https://user-images.githubusercontent.com/29251855/196593224-bf7d2e6a-4dbf-46ae-ab10-4168e8de1014.png)