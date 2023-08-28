---
title: 68-Fully airgapped rancher integrate with harvester with no proxy
---

* Related task: [#1808](https://github.com/harvester/harvester/issues/1808) RKE2 provisioning fails when Rancher has no internet access (air-gapped)

* **Note1**: in fully air gapped environment, you have to setup private docker hub registry and pull all rancher related offline image
* **Note2**: Please use SUSE SLES JeOS image, it have `qemu-guest-agent` already installed, thus the guest VM can get IP correctly

### Environment Setup

Setup the airgapped harvester
1. Fetch ipxe vagrant example with new offline feature
https://github.com/harvester/ipxe-examples/pull/32 
1. Edit the setting.xml file
1. Set offline: `true`
1. Use ipxe vagrant example to setup a 3 nodes cluster
1. Enable vlan on `harvester-mgmt`
1. Now harvester dashboard page will out of work
1. Create virtual machine with name `vlan1` and id: `1`
1. Create ubuntu cloud image from File

#### Phase 1: setup airgap Harvester
1. Set offline: true in [vagrant-pxe-harvester](https://github.com/harvester/ipxe-examples/blob/f75483563f192090dadd48051bbc3b538c30cd34/vagrant-pxe-harvester/settings.yml#L42-L44).
1. Set 1 node harvester with sufficient resources
1. Run ./setup_harvester.sh.

#### Phase 2: Create a virtual machine for Rancher in air gapped environment 
1. Create a virtual machine with at least 300GB storage (OS: Ubuntu Desktop 20.04)
1. Add `harvester` and `vagrant-libvirt` network to the virtual machine  
  - `harvester` for internal 
  - `vagrant-libvirt` for external 

#### Phase 3: Setup a private docker registry and download all the offline images for Rancher 
1. Install VIM
    ```
    sudo apt update
    sudo apt install vim
    ```
1. Install Docker 
    ```
    sudo apt-get update
    sudo apt-get install \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io
    ```
1. Add current user to docker group
    ```
    sudo groupadd docker
    sudo usermod -aG docker $USER
    ```
1. Logout and login again.
1. Install helm
    ```
    curl https://baltocdn.com/helm/signing.asc | sudo apt-key add -
    sudo apt-get install apt-transport-https --yes
    echo "deb https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
    sudo apt-get update
    sudo apt-get install helm
    ```
1. Create certs folder
    ```
    mkdir -p certs
    ```
1. Generate private registry certificate files
    ```
    openssl req \
        -newkey rsa:4096 -nodes -sha256 -keyout certs/domain.key \
        -addext "subjectAltName = DNS:myregistry.test" \
        -x509 -days 365 -out certs/domain.crt
    ```
1. Move certificate files
    ```
    sudo mkdir -p /etc/docker/certs.d/myregistry.test:5000
    sudo cp certs/domain.crt /etc/docker/certs.d/myregistry.test:5000/domain.crt
    ```
1. Start docker registry
    ```
    docker run -d \
        -p 5000:5000 \
        --restart=always \
        --name registry \
        -v "$(pwd)"/certs:/certs \
        -v "$(pwd)"/registry:/var/lib/registry \
        -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
        -e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
        registry:2
    ```
1. Add myregistry.test record. Remember to change your private ip.
    ```
    # vim /etc/hosts
    192.168.0.50 myregistry.test
    ```
1. Create `get-rancher-scripts` script.
    ```
    # vim get-rancher-scripts
    #!/bin/bash
    if [[ $# -eq 0 ]] ; then
        echo 'This requires you to pass a version for the url like "v2.6.3"'
        exit 1
    fi
    wget https://github.com/rancher/rancher/releases/download/$1/rancher-images.txt
    wget https://github.com/rancher/rancher/releases/download/$1/rancher-load-images.sh
    wget https://github.com/rancher/rancher/releases/download/$1/rancher-save-images.sh
    chmod +x ./rancher-save-images.sh
    chmod +x ./rancher-load-images.sh
    ```
1. Make `get-rancher-scripts` can be executed.
    ```
    chmod +x get-rancher-scripts
    ```
1. Get  rancher-images.txt.
    ```
    ./get-rancher-scripts v2.6.4-rc13
    ```
1. Add cert-manager images to rancher-images.txt
    ```
    helm repo add jetstack https://charts.jetstack.io/
    helm repo update
    helm fetch jetstack/cert-manager --version v1.7.1
    helm template ./cert-manager-v1.7.1.tgz | awk '$1 ~ /image:/ {print $2}' | sed s/\"//g >> ./rancher-images.txt
    ```
1. Sort rancher-images.txt
    ```
    sort -u rancher-images.txt -o rancher-images.txt
    ```
1. Get Rancher images. This step may take at least 2 hours depends on your network speed
  ```
  ./rancher-save-images.sh --image-list ./rancher-images.txt
  ```
  ![image](https://user-images.githubusercontent.com/29251855/160348531-f6f5dd3b-af01-43e2-81ae-ab5b47719d7f.png)
  
#### Phase 4: Push the image to docker registry 
1. Download k3s v1.23.4+k3s1
    ```
    wget https://github.com/k3s-io/k3s/releases/download/v1.23.4%2Bk3s1/k3s-airgap-images-amd64.tar
    wget https://github.com/k3s-io/k3s/releases/download/v1.23.4%2Bk3s1/k3s
    chmod +x k3s
    
    sudo cp k3s /usr/local/bin/
    sudo chown $USER /usr/local/bin/k3s
    
    curl https://get.k3s.io/ -o install.sh
    chmod +x install.sh
    ```
1. Download rancher v2.6,4-rc13 helm
    ```
    helm repo add rancher-latest https://releases.rancher.com/server-charts/latest
    helm fetch rancher-latest/rancher --version=v2.6.4-rc13
    ```
1. Download cert-manager crds.
    ```
    mkdir cert-manager
    curl -L -o cert-manager/cert-manager-crd.yaml https://github.com/jetstack/cert-manager/releases/download/v1.7.1/cert-manager.crds.yaml
    ```

1. Install k9s (option)
    ```
    curl -kL https://github.com/derailed/k9s/releases/download/v0.25.18/k9s_Linux_x86_64.tar.gz > k9s.tar.gz
    tar -zxvf k9s.tar.gz
    mv k9s /usr/local/bin/
    ```

1. Cut Network -> Remove the `vagrant-libvirt` network device from virtual machine, make it air gapped
1. Load Rancher images to private registry. 
    ```
    ./rancher-load-images.sh --image-list ./rancher-images.txt --registry myregistry.test:5000
    ```
- This step may take 50 minutes depends on total image size

#### Phase 5: Install K3s and Rancher 
1. Move k3s images files.
    ```
    sudo mkdir -p /var/lib/rancher/k3s/agent/images/
    sudo cp ./k3s-airgap-images-amd64.tar /var/lib/rancher/k3s/agent/images/
    ```
1. Install k3s
  ```
  INSTALL_K3S_SKIP_DOWNLOAD=true ./install.sh
  ```
1. Add `registries.yaml`  to `/etc/rancher/k3s/`
    ```
    # vim /etc/rancher/k3s/registries.yaml
    mirrors:
        docker.io:
        endpoint:
            - "https://myregistry.test:5000/"
    configs:
        "myregistry.test:5000":
        tls:
            insecure_skip_verify: true
    ```
1. Restart k3s
    ```
    sudo systemctl restart k3s.service
    ```
1. Copy kubeconfig to ~/.kube
    ```
    mkdir ~/.kube
    sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
    sudo chown $USER ~/.kube/config
    export KUBECONFIG=~/.kube/config
    ```
1. Generate cert-manager YAML files.
    ```
    helm template cert-manager ./cert-manager-v1.7.1.tgz --output-dir . \
        --namespace cert-manager \
        --set image.repository=myregistry.test:5000/quay.io/jetstack/cert-manager-controller \
        --set webhook.image.repository=myregistry.test:5000/quay.io/jetstack/cert-manager-webhook \
        --set cainjector.image.repository=myregistry.test:5000/quay.io/jetstack/cert-manager-cainjector \
        --set startupapicheck.image.repository=myregistry.test:5000/quay.io/jetstack/cert-manager-ctl
    ```
1. Install cert-manager.
    ```
    kubectl create namespace cert-manager
    kubectl apply -f cert-manager/cert-manager-crd.yaml
    kubectl apply -R -f ./cert-manager
    ```
1. Create CA private key and certifacate file.
    ```
    openssl genrsa -out cakey.pem 2048
    openssl req -x509 -sha256 -new -nodes -key cakey.pem -days 3650 -out cacerts.pem -subj "/CN=cattle-ca"
    ```
1. Create `openssl.cnf`. Remember to change `192.168.0.50` to your private ip.
    ```
    [req]
    req_extensions = v3_req
    distinguished_name = req_distinguished_name
    [req_distinguished_name]
    [ v3_req ]
    basicConstraints = CA:FALSE
    keyUsage = nonRepudiation, digitalSignature, keyEncipherment
    extendedKeyUsage = clientAuth, serverAuth
    subjectAltName = @alt_names
    [alt_names]
    DNS.1 = myrancher.local
    IP.1 = 192.168.0.50
    ```
1. Generate private key and certificate file for `myrancher.local`.
    ```
    openssl genrsa -out tls.key 2048
    openssl req -sha256 -new -key tls.key -out tls.csr -subj "/CN=myrancher.local" -config openssl.cnf
    openssl x509 -sha256 -req -in tls.csr -CA cacerts.pem \
        -CAkey cakey.pem -CAcreateserial -out tls.crt \
        -days 3650 -extensions v3_req \
        -extfile openssl.cnf
    ```
1. Create `cattle-system` namespace.
    ```
    kubectl create ns cattle-system
    ```
1. Create `tls.sa` secret.
    ```
    kubectl -n cattle-system create secret generic tls-ca \
    --from-file=cacerts.pem=./cacerts.pem
    ```
1. Create `tls-rancher-ingress` secret.
    ```
    kubectl -n cattle-system create secret tls tls-rancher-ingress \
    --cert=tls.crt \
    --ke  y=tls.key
    ```
1. Generate Rancher YAML files.
    ```
    helm template rancher ./rancher-2.6.4-rc13.tgz --output-dir . \
        --no-hooks \
        --namespace cattle-system \
        --set hostname=helm-install.local \
        --set rancherImageTag=v2.6.4-rc13 \
        --set rancherImage=myregistry.test:5000/rancher/rancher \
        --set systemDefaultRegistry=myregistry.test:5000 \
        --set useBundledSystemChart=true \
        --set ingress.tls.source=secret \
        --set privateCA=true
    ```
1. Install Rancher 
  ```
  kubectl -n cattle-system apply -R -f ./rancher
  
  davidtclin@davidtclin-Standard-PC-Q35-ICH9-2009:~$ kubectl -n cattle-system apply -R -f ./rancher
  clusterrolebinding.rbac.authorization.k8s.io/rancher created
  deployment.apps/rancher created
  ingress.networking.k8s.io/rancher created
  service/rancher created 
  serviceaccount/rancher created
  
  ```
  ![image](https://user-images.githubusercontent.com/29251855/160362486-4e521a71-9b31-4460-a4a0-958653dbd56d.png)

#### Phase 6: Edit Rancher vm hosts file and boostrap Rancher
1. Edit the `/etc/hosts` file in Rancher virtual machine 
    ```
    192.168.0.50    myregistry.test
    ```
    
1. Edit the `/etc/hosts` file in Host machine
    ```
    192.168.0.50 helm-install.local
    ```
    ![image](https://user-images.githubusercontent.com/29251855/160389038-40cf1803-4914-4dae-83a7-0a547872429f.png)

1. Open browser on your host machine, access the URL https://helm-install.local/ 
    ![image](https://user-images.githubusercontent.com/29251855/160363090-3741cb41-a48e-4512-90ab-0ef2287e27ae.png)
 
1. Copy the the helm command and run in the rancher virtual machine terminal 

1. Get the password and complete the bootstrap process
    ![image](https://user-images.githubusercontent.com/29251855/160363211-980d17a8-8441-45ee-9af2-f4d000ac9c06.png)

#### Phase 7: Edit Harvester cluster hosts files
1. Edit `/etc/hosts` on harvester node machine 
    ```
    # vim /etc/hosts
    192.168.0.50 myregistry.test helm-install.local 
    ```
    ![image](https://user-images.githubusercontent.com/29251855/160390326-d89b5ece-2cab-48bc-a1ee-35fd7f8cc648.png)

1. Set `registries.yaml` in Harvester. /etc/rancher/rke2/registries.yaml
    ```
    # vim /etc/rancher/rke2/registries.yaml
    mirrors:
        docker.io:
        endpoint:
            - "https://myregistry.test:5000/"
    configs:
        "myregistry.test:5000":
        tls:
            insecure_skip_verify: true
    ```
1. Restart Harvester
    ```
    systemctl restart rke2-server.service
    ```

#### Phase 8: Add host mapping to coredns configmap and deployments 
1. Open K9s -> enter `: configmap` -> search dns
    ![image](https://user-images.githubusercontent.com/29251855/160373835-c4aa114e-d07d-4ec6-8ff7-ba742008bf9a.png)
1. Edit the `rke2-coredns-rke2-coredns`
1. Add the following content and save 
    ```
    hosts /etc/coredns/customdomains.db helm-install.local {\n
        \   fallthrough\n    }
    ```

    ```
    customdomains.db: |
        192.168.0.50 helm-install.local
    ```
  
    ```
    data:
        Corefile: ".:53 {\n    errors \n    health  {\n        lameduck 5s\n    }\n    ready
        \n    kubernetes   cluster.local  cluster.local in-addr.arpa ip6.arpa {\n        pods
        insecure\n        fallthrough in-addr.arpa ip6.arpa\n        ttl 30\n    }\n    prometheus
        \  0.0.0.0:9153\n   hosts /etc/coredns/customdomains.db helm-install.local {\n
        \   fallthrough\n    }\n forward   . /etc/resolv.conf\n    cache   30\n    loop
        \n    reload \n    loadbalance \n}"
        customdomains.db: |
        192.168.0.50 helm-install.local
    ```
  
1. Open K9s -> enter `: deployment` -> search dns 
1. Edit the rke2-coredns-rke2-coredns 
  ![image](https://user-images.githubusercontent.com/29251855/160374673-cadbf036-7a76-48c3-8029-306976f69ef0.png)
1. Add the following content and save
    ```
    - key: customdomains.db
                path: customdomains.db
    ```
    ![image](https://user-images.githubusercontent.com/29251855/160374909-e8364442-9401-468f-8c3a-5f7ce9c1443b.png)


#### Phase 9: Import Harvester from Rancher UI
1. Environment preparation as above steps
1. Open Rancher virtualization management page and click import 
  ![image](https://user-images.githubusercontent.com/29251855/160376484-8d4503ab-32e3-4579-bb54-9f317763e795.png)

1. Copy the registration URL and paste in the Harvester cluster URL settings
  ![image](https://user-images.githubusercontent.com/29251855/160376541-8ad0a58b-e118-4748-9e2d-f0a99eeaca2a.png)


### Test steps
After we already made Harvester imported in Rancher, we can use the following steps to Provision an RKE2 guest cluster

1. ssh to the Rancher VM instance
1. (On k3s with Rancher VM), Update coredns in k3s `sudo vim /var/lib/rancher/k3s/server/manifests/coredns.yaml`
1. Update Configmap data to the following
    ```
    # update ConfigMap
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
        192.168.0.50 airgap helm-install.local
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

1. Import `SLES15-SP3-JeOS.x86_64-15.3-OpenStack-Cloud-GM.qcow2` to Harvester (We can also use opensuse leap 15.4 which contains qemu-agent)
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
    - echo 192.168.0.50 helm-install.local helm-install.local >> /etc/hosts
   ```
1. Wait for the guest cluster VM ready on Harvester to expose IP address
1. ssh to the RKE2 guest cluster VM
1. (On the RKE2 guest VM), Create a file in `/etc/rancher/agent/tmp_registries.yaml`:
    ```
    mirrors:
      docker.io:
        endpoint:
          - "https://myregistry.test:5000"
    configs:
      "myregistry.test:5000":
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
1. (On the RKE2 guest VM) Create a file in `/etc/rancher/rke2/registries.yaml`:
    ```
    mirrors:
      docker.io:
        endpoint:
          - "https://myregistry.test:5000"
    configs:
      "myregistry.test:5000":
        tls:
          insecure_skip_verify: true
    ```
1. Check RKE2 cluster provisioning enter into waiting for cluster to join
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
        \  0.0.0.0:9153\n   hosts /etc/coredns/customdomains.db helm-install.local {\n
        \   fallthrough\n    }\n forward   . /etc/resolv.conf\n    cache   30\n    loop
        \n    reload \n    loadbalance \n}"
      customdomains.db: |
        192.168.0.50 helm-install.local
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
  curl -k https://myregistry.local:5000/v2f/rancher/system-agent-installer-rke2/tags/list | jq
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


### Expected Results
1. Can import harvester from Rancher correctly 
1. Can access downstream harvester cluster from Rancher dashboard 
1. Can provision at least one node RKE2 cluster to harvester correctly with running status
1. Can explore provisioned RKE2 cluster nodes 
1. RKE2 cluster VM created running correctly on harvester node