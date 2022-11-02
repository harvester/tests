---
title: Logging Output Filter
---

* Related issues: [#2817](https://github.com/harvester/harvester/issues/2817) [BUG]Logging Output needs filter

  
## Category: 
* Audit Logging

## Verification Steps
1. Create an `Audit Only` type of Output named `audit-output`
    ![image](https://user-images.githubusercontent.com/29251855/193509247-09f5efd9-c43d-4514-bb84-55cd34c243b1.png)
1. Create an `Audit Only` type of ClusterOutput named `audit-cluster-output`
1. Create a Flow, select the type to `Logging` or `Event`
1. Check you **can't** select the `audit-output` and `audiot-cluster-output`
1. select the type to `Audit ` 
1. Check you **can** select the `audit-output` and `audit-cluster-output`
    ![image](https://user-images.githubusercontent.com/29251855/193510780-2f2f6d09-7ee6-433b-80ae-eb3879337513.png)
1. Create a ClusterFlow, select the type to `Logging` or `Event`
1. Check you **can't** select the `audiot-cluster-output`
1. select the type to `Audit`
1. Check you **can** select the `audiot-cluster-output`
1. Create an `logging/event` type of Output named `logging-event-output`
    ![image](https://user-images.githubusercontent.com/29251855/193512327-8ff2cadf-d02d-453f-96e9-fbc7d64ad91f.png)
1. Create an `logging/event` type of ClusterOutput named `logging-event-cluster-output`
    ![image](https://user-images.githubusercontent.com/29251855/193512534-82d03364-b2f2-4bcb-b676-814ab5a9da6d.png)
1. Create a Flow, select the type to `Logging` or `Event`
1. Check you **can** select the `logging-event-output` and `logging-event-output`
1. Create a ClusterFlow, select the type to `Logging` or `Event`
1. Check you **can** select the `logging-event-output` and `logging-event-output`


## Expected Results
1. The `logging` or the `Event` type of `Flow` can only select `Logging` or `Event` type of  `Output` 
    ![image](https://user-images.githubusercontent.com/29251855/193512689-d56ddf11-0db8-4a10-ba9f-0425fb22710d.png)
    ![image](https://user-images.githubusercontent.com/29251855/193512719-4056e234-7e0a-49e4-9503-7bbd75075e0f.png)

1. Can't select the `Audit` type of `Output`
    ![image](https://user-images.githubusercontent.com/29251855/193513555-9b0db18d-8c44-4569-a243-730e751fc042.png)

1. The `logging` or the `Event` type of `ClusterFlow` can only select `Logging` or `Event` type of  `ClusterOutput`
    ![image](https://user-images.githubusercontent.com/29251855/193512859-a905d87c-f23a-4d43-b76e-55f513e2e56c.png)

1. Can't select the `Audit` type of `ClusterOutput`
    ![image](https://user-images.githubusercontent.com/29251855/193513604-8c9cedf6-9236-4595-b0a6-8b12e987ffcc.png)

1. The `Audit` type of `Flow`  can only select `Audit` type of `Output`
    ![image](https://user-images.githubusercontent.com/29251855/193510664-d75963fe-c260-4933-b51b-86b170b512f3.png)
    ![image](https://user-images.githubusercontent.com/29251855/193510896-d189d269-4431-4c25-ab6a-89a9e78225cc.png)

1. The `Audit` type of `ClusterFlow`  can only select `Audit` type of `ClusterOutput`
    ![image](https://user-images.githubusercontent.com/29251855/193511165-d79edca9-9e04-4575-91b3-10d184ce60b4.png)
