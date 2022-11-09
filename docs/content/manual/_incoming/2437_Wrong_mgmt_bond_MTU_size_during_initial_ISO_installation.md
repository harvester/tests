---
title: Wrong mgmt bond MTU size during initial ISO installation
category: console
tag: installer, p2, functional
---
Ref: https://github.com/harvester/harvester/issues/2437

![image](https://user-images.githubusercontent.com/5169694/192757588-73484301-07e7-4a37-9d1e-cbcada9b5774.png)
![image](https://user-images.githubusercontent.com/5169694/192758868-422887df-557c-4d8c-9ee8-2ab0f863f97a.png)


### Verify Steps:
1. Install Harvester via ISO and configure **IPv4 Method** with _static_
1. Inputbox `MTU (Optional)` should be available and optional
1. Configured MTU should reflect to the port's MTU after installation
