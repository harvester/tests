---
title: Clone VM that was created from template	
---

## Case 1
1. Clone VM from Virtual Machine list that was created from template

### Expected Results
1. Machine should start if start VM after creation was checked
1. Machine should match the origin machine
    - in Config
    - In YAML
1. You should be able to connect to new VM via console

## Case 2
1. Clone VM with volume from Virtual Machine list that was created from template 

### Expected Results
1. Before cloning machine create file run command `echo "123" > test.txt && sync`
1. Machine should start if start VM after creation was checked
1. Machine should match the origin machine
    - in Config
    - In YAML
1. You should be able to connect to new VM via console
1. file `test.txt` should exist