---
title: Detach volume from virtual machine
---

* Related issues: [#1708](https://github.com/harvester/harvester/issues/1708) After click "Detach volume" button, nothing happend

## Category: 
* Volume

## Verification Steps
1. Create several new volume in volumes page
![image](https://user-images.githubusercontent.com/29251855/146900871-50fad5fa-2d25-4559-b10b-55e276d7edb8.png)
1. Create a virtual machine
1. Click the config button on the selected virtual machine 
1. Click Add volume and add at least two new volume 
![image](https://user-images.githubusercontent.com/29251855/146901117-dac73494-d8fd-4e1c-9a74-eed76fc14511.png)
1. Click the `Detach volume` button on the attached volume 
![image](https://user-images.githubusercontent.com/29251855/146901585-51df212b-5443-4961-b648-6db265c272c2.png)

![image](https://user-images.githubusercontent.com/29251855/146901235-6607a936-884b-41d9-94e2-372e8c028334.png)
1. Repeat above steps several times 

## Expected Results
Currently when click the **Detach volume** button, attached volume can be detach successfully.  

![image](https://user-images.githubusercontent.com/29251855/146901702-9914241c-60fb-4fc9-a03a-4d72e979e20a.png)

![image](https://user-images.githubusercontent.com/29251855/146901739-7e8d0303-a753-4c02-bb33-fdf7188a65b0.png)

![image](https://user-images.githubusercontent.com/29251855/146901821-3bbc71a3-6f06-4d37-a0e2-53ee0a420f61.png)

