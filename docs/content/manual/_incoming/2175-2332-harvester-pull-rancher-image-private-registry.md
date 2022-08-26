---
title: Harvester pull Rancher agent image from private registry
---

* Related issues: [#2175](https://github.com/harvester/harvester/issues/2175) [BUG] Harvester fails to pull Rancher agent image from private registry
* Related issues: [#2332](https://github.com/harvester/harvester/issues/2332) [Backport v1.0] Harvester fails to pull Rancher agent image from private registry

## Category: 
* Virtual Machine

## Verification Steps
1. Create a harvester cluster and a ubuntu server. Make sure they can reach each other.
2. On each harvester node, add ubuntu IP to `/etc/hosts`.
```
# vim /etc/hosts
<host ip> myregistry.local
```
3. On the ubuntu server, install docker and run the following commands.
```
$ mkdir -p certs
$ openssl req \
  -newkey rsa:4096 -nodes -sha256 -keyout certs/domain.key \
  -addext "subjectAltName = DNS:myregistry.local" \
  -x509 -days 365 -out certs/domain.crt
$ sudo mkdir -p /etc/docker/certs.d/myregistry.local:5000
$ sudo cp certs/domain.crt /etc/docker/certs.d/myregistry.local:5000/domain.crt
$ sudo docker run -d \
  -p 5000:5000 \
  --restart=always \
  --name registry \
  -v "$(pwd)"/certs:/certs \
  -v "$(pwd)"/registry:/var/lib/registry \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
  registry:2
$ sudo docker pull rancher/rancher-agent:v2.6.5
$ sudo docker tag rancher/rancher-agent:v2.6.5 myregistry.local:5000/rancher/rancher-agent:v2.6.5
$ sudo docker push myregistry.local:5000/rancher/rancher-agent:v2.6.5
```

4. Create a rancher v2.6.5 (it's can be a docker container or VM). After it starts, update `system-default-registry` setting to `myregistry.local:5000`
5. Open harvester dashboard and update `additional-ca` setting with content in `~/certs/domain.crt` in ubuntu server.

### Case 1: Import Harvester to Rancher
Import harvester cluster to the rancher and doesn't have any error.
* Check image in `cattle-system/cattle-cluster-agent` deployment is `myregistry.local:5000/rancher/rancher-agent:v2.6.5`.

### Case 2: Reboot Harvester
* Reboot Harvester node and check we still can query `https://myregistry.local:5000`
```
curl https://myregistry.local:5000
```

### Case 3: Add another node to Harvester cluster
* Add another node to harvester cluster and add `192.168.0.50 myregistry.local` to `/etc/hosts`.
* Login to the new node and run the following command. It should not have error.
```
curl https://myregistry.local:5000
```

### Case 4: Remove additional-ca
* Set `additional-ca` setting as default.
* Wait for new `cattle-system/apply-sync-additional-ca-on-xxx` jobs finish.
* Login to any harvester node. It should have `SSL certificate problem` with the following command.
```
curl https://myregistry.local:5000
```

*Please be noted*
1. The Rancher, Docker registry and each harvester node need to add in /etc/hosts 
```
# vim /etc/hosts
{docker registry vm IP} myregistry.local
```
2.  Update the `system-default-registry` setting to myregistry.local:5000 on Rancher global settings 
![image](https://user-images.githubusercontent.com/29251855/173013507-0c87bdbf-5048-46e7-a78d-c667cca7d408.png)

3. In Case 4, if you don't find any `cattle-system/apply-sync-additional-ca-on-xxx`, just proceed to clean up the `additional-ca` setting

## Expected Results
### Case 1: Import Harvester to Rancher

* Import harvester cluster to the rancher and doesn't have any error.
![image](https://user-images.githubusercontent.com/29251855/173025751-1e74e273-c214-4a47-a0f2-3528bf26fb80.png)

* Check image in cattle-system/cattle-cluster-agent deployment is myregistry.local:5000/rancher/rancher-agent:v2.6.5.
![image](https://user-images.githubusercontent.com/29251855/173026211-631df8a0-b2e3-4840-86be-d8d9a14e59d9.png)

### Case 2: Reboot Harvester
* Reboot Harvester node and check we still can query https://myregistry.local:5000


### Case 3: Add another node to Harvester cluster
* Login to the new node and run the following command. It should not have error.
```
node2-220610:~ # curl https://myregistry.local:5000
node2-220610:~ # 

```
### Case 4: Remove additional-ca
* Login to any harvester node. It should have SSL certificate problem with the following command.

```
node1-220610:~ # curl https://myregistry.local:5000
curl: (60) SSL certificate problem: self signed certificate
More details here: https://curl.haxx.se/docs/sslcerts.html

curl failed to verify the legitimacy of the server and therefore could not
establish a secure connection to it. To learn more about this situation and
how to fix it, please visit the web page mentioned above.
```


