---
title: Support private registry for Rancher agent image in Air-gap
---

* Related issues: [#2176](https://github.com/harvester/harvester/issues/2176) [Enhancement] Air-gap operation: Support using a private registry for Rancher agent image

  
## Category: 
* Rancher Integration

## Verification Steps
### Environment Setup
1. Use vagrant-pxe-harvester to create a harvester cluster.
1. Create another VM `myregistry` and set it in the same virtual network.
1. In `myregistry` VM:
    - Install docker.
    - Run following commands:
    ```
    mkdir auth
    docker run \
    --entrypoint htpasswd \
    httpd:2 -Bbn testuser testpassword > auth/htpasswd

    mkdir -p certs

    openssl req \
    -newkey rsa:4096 -nodes -sha256 -keyout certs/domain.key \
    -addext "subjectAltName = DNS:myregistry.local" \
    -x509 -days 365 -out certs/domain.crt

    sudo mkdir -p /etc/docker/certs.d/myregistry.local:5000
    sudo cp certs/domain.crt /etc/docker/certs.d/myregistry.local:5000/domain.crt

    docker run -d \
    -p 5000:5000 \
    --restart=always \
    --name registry \
    -v "$(pwd)"/certs:/certs \
    -v "$(pwd)"/registry:/var/lib/registry \
    -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
    -e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
    -v "$(pwd)"/auth:/auth \
    -e "REGISTRY_AUTH=htpasswd" \
    -e "REGISTRY_AUTH_HTPASSWD_REALM=Registry Realm" \
    -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
    registry:2
    ```
1. Set IP and domain in `/etc/hosts` to all VM (harvester and `myregistry`). Remember to change the IP.
    ```
    # vim /etc/hosts
    192.168.0.50 myregistry.local
    ```
1. Login, pull, and push nginx image in `myregsitry` VM:
    ```
    # username: testuser, password: testpassword
    docker login myregistry.local:5000
    docker pull nginx:latest
    docker tag nginx:latest myregistry.local:5000:/nginx:latest
    docker push myregistry.local:5000/nginx:latest
    docker pull nginx:1.22
    docker tag nginx:latest myregistry.local:5000:/nginx:1.22
    docker push myregistry.local:5000/nginx:1.22
    ```
1. Copy `certs/domain.crt` content in `myregistry` VM and paste it to `additional-ca` setting.

### Test Plan 1
1. Update the Harvester containerd-registry setting to use private registry
    ![image](https://user-images.githubusercontent.com/29251855/193785720-970d9f18-76c6-4818-ae6a-e6239baf8ebe.png)
    ![image](https://user-images.githubusercontent.com/29251855/193785814-02c7b5b5-89da-43f0-a5f5-f36b8609a2df.png)
    ```
    {
    "Mirrors": {
        "docker.io": {
        "Endpoints": [
            "https://myregistry.local:5000"
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
            "InsecureSkipVerify": false
        }
        }
    },
    "Auths": null
    }
    ```
1. Open K9s -> search -> secrets -> containerd -> y
    ![image](https://user-images.githubusercontent.com/29251855/193786543-ed43eb8a-f332-48b9-8b8a-afef8088f97f.png)
1. Check content in cattle-system/harvester-containerd-registry secret is changed. 
    ![image](https://user-images.githubusercontent.com/29251855/193787031-2ea11b68-e79c-4c10-8409-0bb337b5baf8.png)
1. Search jobs -> containerd -> l -> tail
1. Check there are new jobs to auto apply the new containerd-registry setting.
    ![image](https://user-images.githubusercontent.com/29251855/193786463-ca1e1f26-e37b-4e1b-b0d3-5e58b7d47bc1.png)
1. Apply following yaml in file 
        ```
        apiVersion: apps/v1
        kind: Deployment
        metadata:
        name: myregistry-nginx
        spec:
        selector:
            matchLabels:
            image: myregistry-nginx
        template:
            metadata:
            labels:
                image: myregistry-nginx
            spec:
            containers:
                - imagePullPolicy: Always
                image: myregistry.local:5000/nginx:latest
                name: nginx
        ```
        ```
        harvester-node-0:~ # kubectl apply -f deploy.yaml
        deployment.apps/myregistry-nginx created
        
        ```
1. search deployments -> default namespace -> myregsistry-nginx -> describe -> shift + g
1. Check the nginx can be deployed. 

### Test Plan 2
1. Click the `default value` to update the Harvester containerd-registry setting to default empty 
    ![image](https://user-images.githubusercontent.com/29251855/193788085-0b1648d7-ef0e-495e-8898-4f743028f94c.png)
1. In K9s
1. Check content in cattle-system/harvester-containerd-registry secret is changed.
1. Check there are new jobs to auto apply the new containerd-registry setting.
1. Search secrets -> containerd -> e 
1. Clean registry.yaml data field
    ```
    # Please edit the object below. Lines beginning with a '#' will be ignored,
    # and an empty file will abort the edit. If an error occurs while saving this file will be
    # reopened with the relevant failures.
    #
    apiVersion: v1
    data:
        registries.yaml: ""
    kind: Secret
    metadata:
        creationTimestamp: "2022-10-04T08:51:47Z"
        name: harvester-containerd-registry
        namespace: cattle-system
        resourceVersion: "42088"
        uid: 8445547f-430a-474e-9783-dc6b16914eb7
    type: Opaque
    ```
1. Search -> deployments -> find nginx-1.2.2
1. Check cannot pull nginx-1.2.2 image
    ![image](https://user-images.githubusercontent.com/29251855/193790572-d5f5c92e-cbb9-4528-9c01-748d37940bc1.png)


### Test Plan 3
1. Add back the Harvester containerd-registry setting to use private registry again 
    ![image](https://user-images.githubusercontent.com/29251855/193790937-a702730e-cb57-4f16-8950-76372a1859e3.png)
1. Check content in cattle-system/harvester-containerd-registry secret is changed.
    ![image](https://user-images.githubusercontent.com/29251855/193791120-755347db-46d7-427b-9e17-adb77025b7c8.png)
1. Check there are new jobs to auto apply the new containerd-registry setting.
    ![image](https://user-images.githubusercontent.com/29251855/193791283-40985e8a-f450-4766-9f0c-68e708c643cb.png)
1. Check nginx 1.22 deployment is automatically back to running.
    ![image](https://user-images.githubusercontent.com/29251855/193791385-5107385d-66c5-44a3-a298-82c44af929c7.png)

## Expected Results
### Test Result 1
1. Update the Harvester containerd-registry setting with private registry, confirm **can** pull image and **deploy** nginx service correctly from private registry

    ![image](https://user-images.githubusercontent.com/29251855/193785720-970d9f18-76c6-4818-ae6a-e6239baf8ebe.png)
    ![image](https://user-images.githubusercontent.com/29251855/193787642-397ccf3a-144f-4785-9601-12a9017be325.png)
    ![image](https://user-images.githubusercontent.com/29251855/193787780-fc46a061-bbca-4051-839c-c4c092e67414.png)

### Test Result 2
1. Change the Harvester `containerd-registry` to default value, the nginx 1.22 cannot be deployed since no private registry assigned. 

    ![image](https://user-images.githubusercontent.com/29251855/193790572-d5f5c92e-cbb9-4528-9c01-748d37940bc1.png)

### Test Result 3
1. **Add back** the the Harvester containerd-registry setting to private registry, confirm **can** pull image and **deploy** nginx service correctly from private registry

    ![image](https://user-images.githubusercontent.com/29251855/193791385-5107385d-66c5-44a3-a298-82c44af929c7.png)