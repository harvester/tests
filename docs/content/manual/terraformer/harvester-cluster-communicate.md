---
title: Check that you can communicate with the Harvester cluster
---
1. Set the KUBECONFIG env variable with the path of your kubeconfig file
1. Try to import any resource to test the connectivity with the Harvester cluster
For instance, try to import ssh-key with:
`terraformer import harvester -r ssh_key`

## Expected Results
You should see:
```
terraformer import harvester -r ssh_key                                                                                   
2021/08/04 15:18:59 harvester importing... ssh_key
2021/08/04 15:18:59 harvester done importing ssh_key
...
```
And the generated files should appear in `./generated/harvester/ssh_key/`
