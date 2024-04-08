---
title: Fleet support with Harvester
---

## Fleet Support Pathways
1. Fleet Support is enabled out of the box with Harvester, no Rancher integration needed, as Fleet Support does not need any Rancher integration to function
2. Fleet Support can be used from within Rancher w/ Harvester


### Fleet Support w/ Rancher Prerequisites
1. Harvester cluster is imported into Rancher.
2. Rancher Feature Flag `harvester-baremetal-container-workload` is enabled.
3. Harvester cluster is available to view via the Explore Cluster section of Rancher.
4. Explore the Harvester cluster:
    1. Toggle "All Namespaces" to be selected
    2. Search for & "star" (marking favorite for ease of navigation):
        -  Git Repo
        -  Git Job
        -  Git Restrictions

### Fleet Support w/out Rancher Prerequisites
1. An active Harvester Cluster Kubeconfig

### Additional Prerequisites
1. Fork [ibrokethecloud's Harvester Fleet Demo](https://github.com/ibrokethecloud/harvester-fleet-demo/) into your own personal GitHub Repository
2. Take a look at the different [Harvester API Resources](https://docs.harvesterhci.io/v1.2/category/api) as YAML will be scaffolded to reflect those objects respectively

### Additional Prerequisites Airgapped, if desired
1. Have an Airgapped GitLab Server Running somewhere with a Repo that takes the shape of [ibrokethecloud's Harvester Fleet Demo](https://github.com/ibrokethecloud/harvester-fleet-demo/)
(setting up AirGapped GitLab Server is outside of this scope)

### Additional Prerequisites (Private Repository Testing), if desired
1. [Private Git Repo Key](https://fleet.rancher.io/gitrepo-add#adding-private-git-repository), will need to be added to `-n fleet-local` namespace
2. Build a private GitHub Repo
3. Add similar content to what [ibrokethecloud's Harvester Fleet Demo](https://github.com/ibrokethecloud/harvester-fleet-demo/) holds but take into consideration the following ( references: [GitRepo CRD](https://fleet.rancher.io/ref-gitrepo) & [Rancher Fleet Private Git Repo Blurb](https://fleet.rancher.io/gitrepo-add#adding-private-git-repository) ):
    1. building a "separate" SINGLE REPOSITORY ONLY (zero-trust based) SSH Key Via something like:
    ```
        ssh-keygen -t rsa -b 4096 -m pem -C "testing-test-key-for-private-repo-deploy-key@email.com"
        Generating public/private rsa key pair.
        Enter file in which to save the key (/home/mike/.ssh/id_rsa): /home/mike/.ssh/rsa_key_for_private_rancher_fleet_repo_testing
        Enter passphrase (empty for no passphrase):
        Enter same passphrase again:
        Your identification has been saved in /home/mike/.ssh/rsa_key_for_private_rancher_fleet_repo_testing
        Your public key has been saved in /home/mike/.ssh/rsa_key_for_private_rancher_fleet_repo_testing.pub
    ```
    2. adding that key to the `fleet-local` namespace as a secret `kubectl create secret generic ssh-key -n fleet-local --from-file=ssh-privatekey=/home/mike/.ssh/rsa_key_for_private_rancher_fleet_repo_testing --type=kubernetes.io/ssh-auth`
    3. going into your repo's `settings -> deploy keys` and adding that SSH Key you just built as a `deploy key`
    4. you'll need to keep in mind that the `setup.yaml` and similar files will need to shift to reflect the fact you're utilizing a private GitHub Repository, those changes may look similar to (please note: `spec.clientSecretName` to reference your SSH Key that was added to the private repository's settings -> deploy keys && `spec.repo` shifts to hold your `git` based URL/URI not the `https` based one):
    ```yaml
        apiVersion: fleet.cattle.io/v1alpha1
        kind: GitRepo
        metadata:
            name: setup-harvester-cluster
            namespace: fleet-local
        spec:
            branch: main
            insecureSkipTLSVerify: false
            paths:
                - "/vm-image"
            pollingInterval: 15s
            repo: 'git@github.com:irishgordo/sample-private-fleet.git'
            clientSecretName: ssh-key
            targetNamespace: default
            targets:
                - clusterSelector: {}
    ```

### Additional Docs To Familiarize Yourself With:
- [Rancher Fleet's Quickstart](https://fleet.rancher.io/quickstart) and respective Docs

## Non-Rancher-Integration Fleet Support Base Tests, Public Repo
##### Note: this can be expanded to encompass more for automation

#### Test Building A GitRepo Is Successful
1. Utilizing [ibrokethecloud's Harvester Fleet Demo](https://github.com/ibrokethecloud/harvester-fleet-demo/) as a base-layer create a folder called `extra-vm-image`
2. Build a file in the root directory called `test-gitrepo-is-successful-public.yaml`
3. Have it structured similar to:
```yaml
    apiVersion: fleet.cattle.io/v1alpha1
    kind: GitRepo
    metadata:
        name: test-gitrepo-success-public
        namespace: fleet-local
    spec:
        branch: main
        paths:
            - "/extra-vm-image"
        pollingInterval: 15s
        repo: YOUR-HTTPS-REPO-URL
        targetNamespace: default
        targets:
            - clusterSelector: {}
```
4. Build a VM Image File in `/extra-vm-image` called `my-test-public-image.yaml`
5. Have that file structured similar to:
```yaml
    apiVersion: harvesterhci.io/v1beta1
    kind: VirtualMachineImage
    metadata:
        annotations:
            harvesterhci.io/storageClassName: harvester-longhorn
    name: opensuse-default-image
    labels:
        testing: testing-pub-repo-non-rancher
    namespace: default
    spec:
        displayName: provide-a-display-name
        retry: 3
        sourceType: download
        storageClassParameters:
            migratable: "true"
            numberOfReplicas: "3"
            staleReplicaTimeout: "30"
        url: https://-or-http://provide-a-url-of-an-image-like-qcow2-to-download-or-img
```
6. Add, Commit, & Push to your public fork
7. Utilizing the `kubeconfig` from your Harvester cluster, go ahead and create the GitRepo CRD from the `raw.github` link of your `test-gitrepo-is-successful-public.yaml` something similar to: `kubectl create -f https://raw.githubusercontent.com/YOUR-USER-NAME/harvester-fleet-demo/main/test-gitrepo-is-successful-public.yaml`
8. Audit that it built the GitRepo CRD with something like `kubectl get GitRepo -A -o wide` you should see `test-gitrepo-success-public` as an available object
9. In the Harvester UI, you should see the VirtualMachineImage being downloaded

#### Test Updating A GitRepo Resource Is Successful
1. With the same `/extra-vm-image/my-test-public-image.yaml` go ahead and modify it creating a description annotation adding the line of something like:
```yaml
metadata:
  annotations:
    harvesterhci.io/storageClassName: harvester-longhorn
    field.cattle.io/description: "my new description for this VirtualMachineImage that's already been downloaded from the URL earlier for Harvester"
```
2. Git Add, Git Commit, & Git Push that change out to the main branch fork of the repo you're utilizing
3. You should see that within a minute the VirtualMachineImage object you created through the CRD get's a different displayed description, that reflects what you passed in with `field.cattle.io/description`

#### Test a forced Rancher Fleet Sync, Synchronizes Git in Comparison with the Current State of Harvester Cluster
1. Go ahead and delete that VirtualMachineImage from the Harvester UI
2. Ensure it's deleted
3. Hop in with your favorite editor or perhaps a patch file (take this as inspiration), run `kubectl edit GitRepo/test-gitrepo-success-public`
4. be mindful we're utilizing [Rancher Fleet GitRepo Object Properties](https://fleet.rancher.io/ref-gitrepo), but add a line in the yaml under `spec` like:
```yaml
  forceSyncGeneration: 1
```
5. save that edited file
6. watch over a period of time, that "user-deleted" VirtualMachineImage "should" come-back-to-life and exist once again in your Harvester cluster

#### Test Deleting A GitRepo Resource Is Successful
1. from within the root directory of the project go ahead and fire off a `kubectl delete -f test-gitrepo-is-successful-public.yaml`
2. validate that the VirtualMachineImage is deleted
3. validate that the GitRepo does not exist eg, `kubectl get GitRepo -A -o wide`

## Rancher Integration Fleet Support Base Tests, Public Repo
##### Note: this can be expanded to encompass more for automation

#### Test Building A GitRepo Is Successful
1. In Rancher UI under the Harvester Cluster that has been imported with the feature flag of `harvester-baremetal-container-workload` created go ahead and start building a GitRepo
2. Link it to your https:// fork of the repo
3. Specify the paths of `/vm-image` (**NOTE: PLEASE CROSS-CHECK the image URL for the VM Image OpenSuse Image URLs 'Historically' fall-out-of-date very fast due to the nature of new builds being rolled out frequently - you will more than likely want to change the opensuse-image.yaml spec.url beforehand and then pushing to your fork of the repo**), `/keypair`, and `/vm-network` for the first iteration
4. Be sure to make sure to Edit the YAML directly changing:
    1. namespace from `fleet-default` to `fleet-local`
    2. that `targets.clusterSelector` does not have that pre-baked-in-logic and is open ended with `targets.clusterSelector: {}`
5. Watch it respectively in the Harvester UI build out those resources
6. Go back into the GitRepo you created after the keypairs, vm-image, vm-network Harvester objects have been built out and edit it, adding the `/vm-workload` to the path
7. Watch over a period of time the Harvester UI eventually spin up a VM utilizing the provided keypairs, vm-image, vm-network
8. Audit things like GitJobs & GitRestrictions in the Rancher UI

#### Test Updates To Harvester Objects Work
1. Modify anything in either: `/vm-image`, `/keypair`, `/vm-workload`, or `/vm-network` [leverage Harvester API Docs to validate modification of Harvester Object](https://docs.harvesterhci.io/v1.2/category/api)
2. Git Add, Git Commit, & Git Push that change out to your fork
3. Validate the change is reflected within the Harvester Cluster

#### Negative Test: Make Sure User-Created Rancher Resources Are Not Affected
1. Build an RKE2 or RKE1 cluster, utilizing Harvester:
    1. use a separate VirtualMachineImage
    2. use separate keypair (if desired)
    3. use a separate vm-network
2. Ensure that RKE2 / RKE1 comes up with the VMs running on Harvester


#### NOTE: Test Cases Can Also Be Reflected Via Either Private GitHub Repo & ALSO self-hosted GitLab Instance, See Earlier Prerequisites for that load-out