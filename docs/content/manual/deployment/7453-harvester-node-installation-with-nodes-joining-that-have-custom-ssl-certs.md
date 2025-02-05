---
title: Installing Harvester Nodes With Custom SSL CA Certs At Inception
---

* Related issues: [#7453](https://github.com/harvester/harvester/issues/7453) Join fails when using custom CA certs

## Verification Steps
1. Setup Static IPs to be used by 2 Nodes & 1 VIP, for a lab VLAN like VLAN 2012, add to confluence
    - be sure to check that the static address is not currently used with something like an `ping a.b.c.d`
    - be sure to check that inventory doesn't exist and if it does that it is not currently being used by a seeder cluster `kubectl get inventory -n tink-system -o yaml | grep -ie "A.B.C.D"`
2. Allocate 2 Nodes for Use for the Harvester Interactive ISO installation
    - we should be able to allocate the nodes without issue
3. Check each node's:
    - storage
    - boot order if legacy
    - RAID setup
        - HP Smart Storage Administrator possibly
    - anything else that would hinder an install, for instance: Ensure that the Nodes do not need to be reflashed: https://support.hpe.com/hpesc/public/docDisplay?docId=emr_na-a00048622en_us (as that will be a blocker).
4. If Lab Hardware looks good, before starting, on your Host Machine, please build `openssl` content -> https://github.com/harvester/harvester/issues/4603#issuecomment-1759220970 pay attention to where you keep/put that content for step 5
5. Given that you've build SSL CA Certs Customized by VIP that you will be using for the Harvester Cluster "prior" to Install, please take a look at our FileServer's /iso/issue-7453/issue-7453/configuration-yaml-test-issue-7453.yaml, the goal is here, to shape a "new" configuration.yaml for this test run that will house "escaped yaml" but wrapped in JSON like that file shows ex:
```yaml
scheme_version: 1
system_settings:
    ssl-certificates: `{"ca":"", "publicCertificate": "", "privateKey": ""}`
```
6. Given that you have a file on the file-server somewhere that "holds" the cert information for a brand-new Harvester cluster that you will create using 2 nodes provisioning via Interactive ISO Installation, go ahead, boot up the first node, and fill out all the console panels as needed, be sure to "provide" the URL address of the `harvester-configuration.yaml` that you built that references the content of the `ssl-certificates`.
7. Once the First Node is "up" & running, install to the second node, you should ensure that once install happens that on the second node you're not seeing any `x509` errors present and that you can have it connect to the cluster without error