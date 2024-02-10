---
title: Check Harvester CloudInit CRDs within Harvester, Terraform & Rancher
---

* Related issues: [#3902](https://github.com/harvester/harvester/issues/3902) support elemental cloud-init via harvester-node-manager

## Testing With Terraform
1. TBD

## Testing From Harvester UI
1. TBD

## Testing From Rancher Fleet UI / Harvester Fleet Controller
1. TBD

## Testing w/ Harvester Kubeconfig via Kubectl & K9s (or similar tool)

### Pre-Reqs:
- Have an available multi-node Harvester cluster, w/out your ssh-key present on any nodes
- Provision cluster however is easiest
- K9s (or other similar kubectl tooling)
- kubectl
- audit [elemental toolkit](https://rancher.github.io/elemental-toolkit/docs/customizing/stages) for an understanding of stages
- audit [harvester configuration](https://docs.harvesterhci.io/v1.2/install/harvester-configuration) to correlate properties to elemental-toolkit based stages / functions

### Negative Tests:

#### Validate Non-YAML Files Get .yaml as Suffix On File-System
1. Prepare a YAML loadout of a CloudInit resource that takes the shape of:
```yaml
apiVersion: node.harvesterhci.io/v1beta1
kind: CloudInit
metadata:
  name: write-file-with-non-yaml-filename
spec:
  matchSelector: {}
  filename: 99_filewrite.log
  contents: |
    stages:
      fs:
        - name: "write file test"
          commands:
            - echo "hello, there" > /etc/sillyfile.conf
```
2. Log on to any one of the nodes in the cluster and validate:
  1. `99_filewrite.log.yaml` is present within `/oem/` directory on the node
  2. the contents of `99_filewrite.log.yaml` look appropriate
3. Validate that `kubectl describe cloudinits/write-file-with-non-yaml-filename` looks appropriate
4. Delete the CloudInit CRD via `kubectl delete cloudinits/write-file-with-non-yaml-filename`

#### Validate Filename with non specified suffix ends up as .yaml
1. Prepare a YAML loadout of a CloudInit resource that takes the shape of:
```yaml
apiVersion: node.harvesterhci.io/v1beta1
kind: CloudInit
metadata:
  name: write-file-with-non-suffix-filename
spec:
  matchSelector: {}
  filename: 99_filewrite
  contents: |
    stages:
      fs:
        - name: "write file test"
          commands:
            - echo "hello, there" > /etc/sillyfile.conf
```
2. Log on to any one of the nodes in the cluster and validate:
    1. `99_filewrite.yaml` is present within `/oem/` directory on the node
    2. the contents of `99_filewrite.yaml` look appropriate
3. Validate that `kubectl describe cloudinits/write-file-with-non-suffix-filename` looks appropriate
4. Delete the CloudInit CRD via `kubectl delete cloudinits/write-file-with-non-suffix-filename`

#### Validate That Non-YAML CloudInit CRD is Rejected
1. Prepare a YAML loadout of a CloudInit resource that takes the shape of:
```yaml
apiVersion: node.harvesterhci.io/v1beta1
kind: CloudInit
metadata:
  name: consolelogoverwrite
spec:
  matchSelector: {}
  filename: install/console.log
  contents: |
    hello  there
```
2. When trying to apply the YAML, it should be rejected at a Webhook level, test via: `kubectl create -f your-file-name.yaml`
3. Validate that is rejected.

### Positive Tests:

#### Validate that a CloudInit Resource Gets Applied Cluster Wide
1. Prepare a YAML loadout of a CloudInit resource that takes the shape of:
```yaml
apiVersion: node.harvesterhci.io/v1beta1
kind: CloudInit
metadata:
  name: ssh-access-test
spec:
  matchSelector: {}
  filename: 99_ssh_test_cluster_wide.yaml
  contents: |
    stages:
      network:
        - authorized_keys:
            rancher:
              - ATTACH-YOUR-SSH-KEY-HERE
```
2. Apply it to the cluster via `kubectl create -f filename.yaml`
3. Validate that the CloudInit Resource was scaffolded appropriately `kubectl describe cloudinits/ssh-access-test`
4. Reboot all nodes in the cluster
5. Once nodes are rebooted validate that you can log in to each node via the SSH Key provided.
6. Delete the CRD `kubectl delete cloudinits/ssh-access-test`
7. Remove the ssh-key entry from `/home/rancher/.ssh/authorized_keys` on each node
8. Reboot the nodes
9. Ensure that the `/oem/99_ssh_test_cluster_wide.yaml` is not present on any node

#### Validate that a CloudInit Resource that targets a Single Node Is Applied Correctly
1. Prepare a YAML loadout of a CloudInit resource that takes the shape of:
```yaml
apiVersion: node.harvesterhci.io/v1beta1
kind: CloudInit
metadata:
  name: ssh-access-test-one-node
spec:
  matchSelector:
    kubernetes.io/hostname: NOTE-FOR-THIS-FIELD change to be the Node Name like for instance-> harvester-node-0
  filename: 99_ssh_test_single_node.yaml
  contents: |
    stages:
      network:
        - authorized_keys:
            rancher:
              - ATTACH-YOUR-SSH-KEY-HERE
```
2. Apply it to the cluster via `kubectl create -f filename.yaml`
3. validate that the CloudInit resource was built appropriately `kubectl describe cloudinits/ssh-access-test-one-node`
4. Reboot the node that has the host-name filed in, as in the node tied to `kubernetes.io/hostname`
5. Validate that you can ssh as rancher onto the node that was rebooted without the need for password
6. Delete the CRD `kubectl delete cloudinits/ssh-access-test-one-node`
7. Remove the ssh-key from `/home/rancher/.ssh/authorized_keys`
8. Reboot the node
9. Validate that the file `/oem/99_ssh_test_single_node.yaml` is not present in the `/oem` directory on that single node

#### Validate that custom labels are reflected upon reboot of nodes with CloudInit Resource
1. On two or more nodes in your multi-node cluster, create a label on each host of something like `testingmode: testing`
2. Prepare a YAML loadout of a CloudInit resource that takes the shape of:
```yaml
apiVersion: node.harvesterhci.io/v1beta1
kind: CloudInit
metadata:
  name: write-file-reflects-nodes
spec:
  matchSelector:
    testingmode: testing
  filename: 99_filewrite_nodes.yaml
  contents: |
    stages:
      fs:
        - name: "write file test reflects nodes"
          commands:
            - echo "hello, there" > /etc/sillyfile.conf
```
3. validate that the cloudinit resource was built correctly `kubectl describe cloudinits/write-file-reflects-nodes`
4. Check the nodes applied to, to make sure `/oem/99_filewrite_nodes.yaml` is present, if not you may need to wait for the controller to reconcile the label logic on the nodes
4. Reboot all nodes that had the label applied
5. Log into each node and ensure that `sudo cat /etc/sillyfile.conf` exists.
6. Remove or modify the label on one of the nodes.
7. Reboot that node.
7. Validate that the `/oem/99_filewrite_nodes.yaml` file is removed, you may need to wait for a bit for the controller to reconcile something like `watch -n 3 ls -alh /oem` as it may take sometime
8. Reboot that node again.
9. Once node is back up validate that `/etc/sillyfile.conf` no longer exists on the node.

#### Validate that CloudInit CRD respects pausing being turned on
1. On a single node in the cluster have a label you can reference it by, this could be something like `kubernetes.io/hostname`
2. Prepare a YAML file that takes the shape of something like:
```yaml
apiVersion: node.harvesterhci.io/v1beta1
kind: CloudInit
metadata:
  name: silly-file-one-node-no-changes
spec:
  matchSelector:
    kubernetes.io/hostname: harvester-node-0
  paused: false
  filename: 99_filewrite_singlenode_wont_get_changes.yaml
  contents: |
    stages:
      fs:
        - name: "write file test reflects nodes"
          commands:
            - echo "hello, there" > /etc/sillyfile-that-doesnt-get-changes.conf
```
3. Apply the resource `kubectl create -f`
4. Reboot the node
5. Check that the node has the file `cat /etc/sillyfile-that-doesnt-get-changes.conf`
6. Patch the file with YAML that takes the shape of something like ( `kubectl patch --patch-file your-filepath/filename.yaml cloudinits/silly-file-one-node-no-changes --type=merge` ):
```yaml
apiVersion: node.harvesterhci.io/v1beta1
kind: CloudInit
metadata:
  name: silly-file-one-node-no-changes
spec:
  matchSelector:
    kubernetes.io/hostname: harvester-node-0
  paused: true
  filename: 99_filewrite_singlenode_wont_get_changes.yaml
  contents: |
    stages:
      fs:
        - name: "write file test reflects nodes"
          commands:
            - echo "hello, there NEW CHANGES" > /etc/sillyfile-that-doesnt-get-changes.conf
```
7. Audit that paused is turned on `kubectl describe cloudinits/silly-file-one-node-no-changes`
8. Reboot the node
9. Ensure that `cat /etc/sillyfile-that-doesnt-get-changes.conf` did not receive the new text of `NEW CHANGES` within it, since `pause` boolean was toggled on CRD