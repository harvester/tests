---
title: SSL Certificate
---
Ref: https://github.com/harvester/harvester/issues/761

## Verify Items
 - generated kubeconfig is able to access kubenetes API
 - new node able to join the cluster using the configured Domain Name
 - create node with ssl-certificates settings is working as expected.

### Case: Kubeconfig
1. Install Harvester with at least 2 nodes
2. Generate self-signed TLS certificates from https://www.selfsignedcertificate.com/ with specific name
3. Navigate to advanced settings, edit `ssl-certificates` settings
4. Update generated `.cert` file to _CA_ and _Public Certificate_, `.key` file to _Private Key_
5. Relogin with domain name
6. Navigate to Support page, then Click **Download KubeConfig**, file should named `local.yaml`
7. Kubernetes API should able to be accessed with config `local.yaml`  (follow one of the [instruction](https://kubernetes.io/docs/tasks/administer-cluster/access-cluster-api/) for testing)

### Case: Host joining with https and Domain Name
1. Install Harvester with single node
2. Generate self-signed TLS certificates from https://www.selfsignedcertificate.com/ with specific name
3. Navigate to advanced settings, edit `ssl-certificates` settings
4. Update generated `.cert` file to _CA_ and _Public Certificate_, `.key` file to _Private Key_
5. Install another Harvester Host as a joining node via PXE installation
    - the `server_url` MUST be configured as the specific domain name
    - Be aware set `os.dns_nameservers` to make sure the domain name is reachable.
6. The joining node should joined to the cluster successfully.

### Case: Host creating with SSL certificates
1. Install Harvester with single node via PXE installation
   - fill in `system_settings.ssl-certificates` as the format in https://github.com/harvester/harvester/issues/761#issuecomment-993060101
2. Dashboard should able to be accessed via VIP and domain name
