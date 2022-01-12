---
title: PXE instll without iso_url field	
---

* Related issues: [#1439](https://github.com/harvester/harvester/issues/1439) PXE boot installation doesn't give an error if iso_url field is missing

## Environment setup
This is easiest to test with the vagrant setup at https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-harvester
1. edit https://github.com/harvester/ipxe-examples/blob/main/vagrant-pxe-harvester/ansible/roles/harvester/templates/config-create.yaml.j2#L27 to be blank

## Verification Steps
1. Run the vagrant `./setup.sh` from the vagrant repo

## Expected Results
1. You should get an error in the console for the VM when installing

