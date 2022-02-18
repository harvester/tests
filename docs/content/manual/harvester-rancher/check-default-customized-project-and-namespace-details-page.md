---
title: Check default and customized project and namespace details page
---

 * Related issue: [#1574](https://github.com/harvester/harvester/issues/1574) Multi-cluster projectNamespace details page error

## Category: 
* Rancher Integration

## Environment setup
1. Install rancher `2.6.3` by docker
```
docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:v2.6.3
```

## Verification Steps
1. Import harvester from rancher dashboard
1. Access harvester from virtualization management page
1. Create several new projects
1. Create several new namespaces under each new projects
1. Access all default and self created namespace
1. Check can display namespace details 
1. Check all new namespaces can display correctly under each projects

## Expected Results
1. Access harvester from rancher virtualization management page
   Click any namespace in the Projects/Namespace can display details correctly with no page error

Default namespace
![image](https://user-images.githubusercontent.com/29251855/143835124-6f81b902-e0b1-4cbd-8e1f-e818ee033fdb.png)

Customized namespace
![image](https://user-images.githubusercontent.com/29251855/143835686-ac125432-568b-426b-8612-c861585eaab2.png)


![image](https://user-images.githubusercontent.com/29251855/143835629-b4913167-b447-4a20-af4a-8ac5452eee62.png)

1. Newly created namespace will display under project list 
![image](https://user-images.githubusercontent.com/29251855/143833328-8e9e3009-22b2-4fed-a6e3-6116ca748a7b.png)