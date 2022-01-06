---
title: Cluster TLS customization
---
Ref: https://github.com/harvester/harvester/issues/1046

## Verify Items
  - Cluster's SSL/TLS parameters could be configured in install option
  - Cluster's SSL/TLS parameters could be updated in dashboard


## Case: Configure TLS parameters in dashboard
1. Install Harvester with any nodes
1. Navigate to Advanced Settings, then edit `ssl-parameters`
1. Select **Protocols** `TLSv1.3`, then save
1. execute command `echo QUIT | openssl s_client -connect <VIP>:443 -tls1_2 | grep "Cipher is"`
1. Output should contain `error...SSL routines...` and `Cipher is (NONE)`
1. execute command `echo QUIT | openssl s_client -connect <VIP>:443 -tls1_3 | grep "Cipher is"`
1. Output should contain `Cipher is <one_of_TLS1_3_Ciphers>`[^1] and should not contain `error...SSL...`
1. repeat Step 2, then select **Protocols** to `TLSv1.2` only, and input **Ciphers** `ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256`
1. execute command `echo QUIT | openssl s_client -connect <VIP>:443 -tls1_2 -cipher 'ECDHE-ECDSA-AES256-GCM-SHA384' | grep "Cipher is"`
1. Output should contain `error...SSL routines...` and `Cipher is (NONE)`

[^1]: TLSv1.3 supported cipher suites: `TLS_AES_128_GCM_SHA256`, `TLS_AES_256_GCM_SHA384`, `TLS_CHACHA20_POLY1305_SHA256`, `TLS_AES_128_CCM_SHA256`, `TLS_AES_128_CCM_8_SHA256`


## Case: Configure TLS parameters in install configuration
1. Install harvester with PXE installation, set `ssl-parameters` in `system_settings` (see the _example_ for more details)
1. Harvester should be installed successfully
1. Dashboard's **ssl-parameters** should be configured as expected

```
# example for ssl-parameters configure option
system_settings:
  ssl-parameters: |
    {
      "protocols": "TLSv1.3",
      "ciphers": "TLS-AES-128-GCM-SHA256:TLS-AES-128-CCM-8-SHA256"
    }
```
