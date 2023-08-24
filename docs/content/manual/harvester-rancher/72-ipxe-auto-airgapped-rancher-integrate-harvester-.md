---
title: 72-Use ipxe example to test fully airgapped rancher integration
---

* Related task: [#1808](https://github.com/harvester/harvester/issues/1808) RKE2 provisioning fails when Rancher has no internet access (air-gapped)

* **Note1**: In this test, we use [vagrant-pxe-airgap-harvester](https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-airgap-harvester) to automatically provide the fully airgapped environment
* **Note1**: Compared to test case 68, we don't need to manually create a separate VM for the Rancher instance and docker private registry, all the prerequisite environment can be done with the `vagrant-pxe-airgap-harvester` solution


### Environment Setup

#### Phase 1: Create airgapped Harvester cluster, Rancher and private registry
1. Clone the latest [ipxe-example](https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-airgap-harvester) which include the `vagrant-pxe-airgap-harvester`
1. Follow the `Sample Host Loadout` and `Prerequisites` in [readme](https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-airgap-harvester) to prepare the prerequisite package
1. If you use `Opensuse Leap` operating system, you may need to comment out the following line in `Vagrantfile` file
    ```
    # libvirt.loader = '/usr/share/qemu/OVMF.fd'
    ```
1. Edit the `settings.yml`, confirm the `image file url`, `harvester_cluster_nodes`, `cpu`, `memory` and `disk` usage
1. Check the `rancher_version` and `rancher_version_no_prefix` meet your requirement
1. If you have plan to upgrade Rancher version, you also need to increase the size of `node_disk_size`
1. Run `./setup_harvester.sh -c` to start provisioning the airgapped infrastructure
1. If you encounter failure like `apt get update`, please check your ansible and vagrant plugin version can meet the `Prerequisite`. You could also check the `Ansible Galaxy's Community General module` have been corrected installed or not

**Please be noted**: the entire provisioning process would take around **six** hours depending on the network bandwith


#### Phase 2: Configure Harvester
1. Once the provisioning complete
1. Create a vm network `vlan1` on `mgmt` cluster network config
1. Import `SLES15-SP3-JeOS.x86_64-15.3-OpenStack-Cloud-GM.qcow2` to Harvester (We can also use opensuse leap 15.4 which contains qemu-agent)

#### Phase 3: Import Harvester from Rancher UI
1. Access Harvester dashboard
1. Open the `containerd-registry ` in settings
1. Add the following Mirrors and Configs 
    ![image](https://github.com/harvester/harvester/assets/29251855/a08d6163-f2b1-4e2e-8638-4607ab8f69d1)

    ![image](https://github.com/harvester/harvester/assets/29251855/e301707e-023d-44e4-b416-ca76d34715df)
    ```
    {
        "Mirrors": {
            "docker.io": {
            "Endpoints": [
                "myregistry.local:5000"
            ],
            "Rewrites": null
            }
        },
        "Configs": {
            "myregistry.local:5000": {
            "Auth": null,
            "TLS": {
                "CAFile": "",
                "CertFile": "",
                "KeyFile": "",
                "InsecureSkipVerify": true
            }
            }
    },
    "Auths": null
    }
    ```
1. Open Rancher virtualization management page and click import 

1. Copy the registration URL and paste in the Harvester cluster URL settings



### Test steps
After we already made Harvester imported in Rancher, we can use the following steps to Provision an RKE2 guest cluster

* User credential to access Harvester dashboard (`admin/testtesttest`)
* User credential to access Rancher dashboard (`admin/rancher`)
* ssh credential to access Harvester node (`rancher/p@ssword`)
* ssh credential to access Rancher VM (`vagrant/vagrant`)


1. ssh to the Rancher VM instance
    ```
    $ ssh vagrant@192.168.2.34 (password: vagrant)
    ```
1. (On k3s with Rancher VM), Update coredns in k3s `sudo vim /var/lib/rancher/k3s/server/manifests/coredns.yaml`
1. Update Configmap data to the following
    ```
    data:
      Corefile: |
        .:53 {
            errors
            health
            ready
            kubernetes cluster.local in-addr.arpa ip6.arpa {
              pods insecure
              fallthrough in-addr.arpa ip6.arpa
            }
            hosts /etc/coredns/customdomains.db {
              fallthrough
            }
            prometheus :9153
            forward . /etc/resolv.conf
            cache 30
            loop
            reload
            loadbalance
        }
        import /etc/coredns/custom/*.server
      customdomains.db: |
        192.168.2.34 rancher-vagrant-vm.local
    ```
1.  Update deployment -> volumes, remove the NodeHost key and path, change with `    customdomains.db`
    ```
      volumes:
        - name: config-volume
          configMap:
            name: coredns
            items:
            - key: Corefile
              path: Corefile
            - key: customdomains.db
              path: customdomains.db
    ```

1. Ensure the `SLES15-SP3-JeOS.x86_64-15.3-OpenStack-Cloud-GM.qcow2` already imported in Harvester (We can also use opensuse leap 15.4 which contains qemu-agent)
1. Provision the RKE2 cluster, on the creation page add the following userData in advanced
    ```
    #cloud-config
    password: 123456
    chpasswd: { expire: False }
    ssh_pwauth: True
    runcmd:
    - - systemctl
        - enable
        - '--now'
        - qemu-guest-agent
    bootcmd:
    - echo 192.168.2.34 myregistry.local rancher-vagrant-vm.local >> /etc/hosts
    ```
    ![image](https://github.com/harvester/harvester/assets/29251855/97cb34ea-1880-4db5-8fb5-9b3f0c4aadad)

1. Wait for the guest cluster VM ready on Harvester to expose IP address
    ![image](https://github.com/harvester/harvester/assets/29251855/12917df6-85c7-4ca5-8fae-e3d580fb092c)

1. ssh to the RKE2 guest cluster VM
1. Wait for the /etc/rancher folder created in provisioning
1. (On the RKE2 guest VM), Create a file in `/etc/rancher/agent/tmp_registries.yaml`:
    ```
    mirrors:
      docker.io:
        endpoint:
          - "https://myregistry.local:5000"
    configs:
      "myregistry.local:5000":
        tls:
          insecure_skip_verify: true
    ```
1. (On the RKE2 guest VM), Update rancher-system-agent config file `/etc/rancher/agent/config.yaml`.
    ```
    agentRegistriesFile: /etc/rancher/agent/tmp_registries.yaml
    ```
1. (On the RKE2 guest VM) Restart rancher-system-agent.
    ```
    systemctl restart rancher-system-agent.service
    ```
1. The provisioning failure will fixed and proceed
    ![image](https://github.com/harvester/harvester/assets/29251855/df6807ec-44a9-47e9-abdc-d4a61a8f6f4c)

1. (On the RKE2 guest VM) Create a file in `/etc/rancher/rke2/registries.yaml`:
    ```
    mirrors:
      docker.io:
        endpoint:
          - "https://myregistry.local:5000"
    configs:
      "myregistry.local:5000":
        tls:
          insecure_skip_verify: true
    ```
1. Check the rke2-server.service is up and running
    ```
    sudo systemctl status rke2-server.service
    ```
1. if you rke2-server failed to start, you can check the /etc/hosts file on the guest cluster machine
1. Check RKE2 cluster provisioning enter into `Waiting for cluster agent to connect`
    ![image](https://github.com/harvester/harvester/assets/29251855/9b44e2b4-ed13-492b-b821-b7b1671ee7aa)
1. Get the kubectl command on RKE2 VM
    ```
    export KUBECONFIG=/etc/rancher/rke2/rke2.yaml
    /var/lib/rancher/rke2/bin/kubectl get nodes

    NAME                               STATUS   ROLES                              AGE     VERSION
    rke2-v12316-pool1-43416171-x2l8f   Ready    control-plane,etcd,master,worker   7h52m   v1.23.16+rke2r1
    ```
1. (On the RKE2 guest VM) Update ConfigMap `kube-system/rke2-coredns-rke2-coredns` in RKE2.

    ```
    ./kubectl get configmaps -A
    ./kubectl edit configmaps rke2-coredns-rke2-coredns -n kube-system
    ```
    ```
    data:
      Corefile: ".:53 {\n    errors \n    health  {\n        lameduck 5s\n    }\n    ready
        \n    kubernetes   cluster.local  cluster.local in-addr.arpa ip6.arpa {\n        pods
        insecure\n        fallthrough in-addr.arpa ip6.arpa\n        ttl 30\n    }\n    prometheus
        \  0.0.0.0:9153\n   hosts /etc/coredns/customdomains.db rancher-vagrant-vm.local {\n
        \   fallthrough\n    }\n forward   . /etc/resolv.conf\n    cache   30\n    loop
        \n    reload \n    loadbalance \n}"
      customdomains.db: |
        192.168.2.34 rancher-vagrant-vm.local
    ```
1. (On the RKE2 guest VM) Update Deployment `kube-system/rke2-coredns-rke2-coredns`.
    ```
    ./kubectl get deployments -A
    ./kubectl edit deployments rke2-coredns-rke2-coredns -n kube-system
    ```
    ```
    # add following to volumes[].configMap
      volumes:
      - configMap:
          defaultMode: 420
          items:
          - key: Corefile
            path: Corefile
          - key: customdomains.db
            path: customdomains.db
          name: rke2-coredns-rke2-coredns
        name: config-volume

    ```
1. We can check the pod status to confirm all relative pods are recreating. And finally we could have the following pods running
    ```
    rke2-v12316-pool1-43416171-x2l8f:/var/lib/rancher/rke2/bin # ./kubectl get pods -A
    NAMESPACE             NAME                                                              READY   STATUS              RESTARTS        AGE
    calico-system         calico-kube-controllers-c6b87769c-hffq8                           1/1     Running             0               5h55m
    calico-system         calico-node-whndb                                                 1/1     Running             0               5h55m
    calico-system         calico-typha-74756dc885-fl5jt                                     1/1     Running             0               5h55m
    cattle-fleet-system   fleet-agent-7bbcf895fd-jkbk8                                      1/1     Running             0               9m10s
    cattle-system         apply-system-agent-upgrader-on-rke2-v12316-pool1-43416171-vlxlq   0/1     Completed           0               8m29s
    cattle-system         cattle-cluster-agent-6d94b9674b-hdtl6                             1/1     Running             0               10m
    cattle-system         system-upgrade-controller-79885c67d5-7b74n                        1/1     Running             0               9m10s
    kube-system           etcd-rke2-v12316-pool1-43416171-x2l8f                             1/1     Running             0               5h57m
    kube-system           harvester-cloud-provider-67589589b-nsftg                          1/1     Running             0               5h55m
    kube-system           harvester-csi-driver-controllers-86ccc7f485-4r8x5                 3/3     Running             0               5h55m
    kube-system           harvester-csi-driver-controllers-86ccc7f485-5hrxc                 3/3     Running             0               5h55m
    kube-system           harvester-csi-driver-controllers-86ccc7f485-hc622                 3/3     Running             0               5h55m
    kube-system           harvester-csi-driver-wz7lt                                        2/2     Running             0               5h54m
    kube-system           helm-install-harvester-cloud-provider-thqg2                       0/1     Completed           0               5h57m
    kube-system           helm-install-harvester-csi-driver-9ftrf                           0/1     Completed           0               5h57m
    kube-system           helm-install-rke2-calico-crd-p7tj6                                0/1     Completed           0               5h57m
    kube-system           helm-install-rke2-calico-zh7b8                                    0/1     Completed           2               5h57m
    kube-system           helm-install-rke2-coredns-7bdr7                                   0/1     Completed           0               5h57m
    kube-system           helm-install-rke2-ingress-nginx-rm2c7                             0/1     Completed           0               5h57m
    kube-system           helm-install-rke2-metrics-server-vrq4q                            0/1     Completed           0               5h57m
    kube-system           kube-apiserver-rke2-v12316-pool1-43416171-x2l8f                   1/1     Running             0               5h56m
    kube-system           kube-controller-manager-rke2-v12316-pool1-43416171-x2l8f          1/1     Running             1 (5h56m ago)   5h57m
    kube-system           kube-proxy-rke2-v12316-pool1-43416171-x2l8f                       1/1     Running             0               5h57m
    kube-system           kube-scheduler-rke2-v12316-pool1-43416171-x2l8f                   1/1     Running             1 (5h56m ago)   5h57m
    kube-system           rke2-coredns-rke2-coredns-78946844cc-7kf57                        1/1     Running             0               14m
    kube-system           rke2-coredns-rke2-coredns-autoscaler-695f789679-5vrzm             1/1     Running             0               5h55m
    kube-system           rke2-ingress-nginx-controller-qr6ml                               0/1     ContainerCreating   0               5h51m
    kube-system           rke2-metrics-server-f969c4b85-skc5c                               1/1     Running             0               5h54m
    tigera-operator       tigera-operator-7765f9f56-vnwdd                                   1/1     Running  
    ```
### Troubleshooting
Query the images to check whether the specific kubernetes version package is supported

Please ensure your client can route to the RKE2 guest cluster VM

* Check rke2-runtime 
  ```
  curl -k https://myregistry.local:5000/v2/rancher/rke2-runtime/tags/list | jq
  ```
* Check system-agent-installer
  ```
  curl -k https://myregistry.local:5000/v2/rancher/system-agent-installer-rke2/tags/list | jq
  ```

If encounter failure, we can also check the following service logs for more details

* Check rancher-system-agent log
  ```
  journalctl -u rancher-system-agent.service --follow
  ```
* Check rke2-server log
  ```
  journalctl -u rke2-server.service --follow
  ```

Restart related service
* Restart rancher-system-agent service
    ```
    systemctl restart rancher-system-agent.service
    ```
* Restart rke2-server service
    ```
    systemctl restart rke2-server.service
    ```

### Expected Results
1. Can import harvester from Rancher correctly 
1. Can access downstream harvester cluster from Rancher dashboard 
1. Can provision at least one node RKE2 cluster to harvester correctly with running status
    ![image](https://github.com/harvester/harvester/assets/29251855/8f256256-849a-45a7-81c3-6741f7afc3b4)

1. Can explore provisioned RKE2 cluster nodes 
1. RKE2 cluster VM created running correctly on harvester node