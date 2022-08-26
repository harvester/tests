---
title: Image upload does not start when HTTP Proxy is configured
---

* Related issues: [#2436](https://github.com/harvester/harvester/issues/2436) [BUG] Image upload does not start when HTTP Proxy is configured
* Related issues: [#2524](https://github.com/harvester/harvester/issues/2524) [backport v1.0] [BUG] Image upload does not start when HTTP Proxy is configured

## Category: 
* Image

## Verification Steps
1. Clone ipxe-example vagrant project https://github.com/harvester/ipxe-examples
1. Edit settings.yml
1. Set `harvester_network_config.offline=true`
1. Create a one node air gapped Harvester with a HTTP proxy server 
1. Access Harvester settings page 
1. Add the following http proxy configuration
  ```
  {
    "httpProxy": "http://192.168.0.254:3128",
    "httpsProxy": "http://192.168.0.254:3128",
    "noProxy": "localhost,127.0.0.1,0.0.0.0,10.0.0.0/8,cattle-system.svc,192.168.0.0/16,.svc,.cluster.local,example.com"
  }
  ```
  ![image](https://user-images.githubusercontent.com/29251855/180407430-bfe9140b-b0c1-44dc-9463-a478a6f705d3.png)

1. Wait for 5 minutes for Harvester to apply the network setting
1. Go to images page
1. Upload image from local file 


## Expected Results
After the HTTP proxy is configured, we can upload image from local file correctly without error
  ![image](https://user-images.githubusercontent.com/29251855/180407064-80c164ff-a46c-413d-ba8b-2a1bea023227.png)
  ![image](https://user-images.githubusercontent.com/29251855/180407214-0600cee9-28ce-46bd-b177-4f0151a5963b.png)




