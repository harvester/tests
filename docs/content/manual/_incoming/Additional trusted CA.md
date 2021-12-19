---
title: Additional trusted CA configure-ability
---
Ref: https://github.com/harvester/harvester/issues/1260

## Verify Items
- Image download with self-signed additional-ca
- VM backup with self-signed additional-ca

### Case: Image downlaod
1. Install Harvester with ipxe-example which includes https://github.com/harvester/ipxe-examples/pull/36
2. Upload any valid iso to **pxe-server**'s `/var/www/`
3. Use Browser to access `https://<pxe-server-ip>/<iso-file>` should be valid
4. Add self-signed cert to Harvester
    - Navigate to Harvester _Advanced Settings_, edit _additional-ca_
    - cert content can be retrieved in pxe-server `/etc/ssl/certs/nginx-selfsigned.crt`
5. Create Image with the same URL `https://<pxe-server-ip>/<iso-file>`
6. Image should be downloaded

### Case: VM backup
1. Install Harvester with ipxe-example
2. setup **Minio** in pxe-server
    - follow [instruction](https://docs.min.io/docs/minio-quickstart-guide.html) to download binary and start the service
    - login to UI console then add region and create bucket
    - follow [instruction](https://docs.min.io/docs/how-to-secure-access-to-minio-server-with-tls.html#using-open-ssl) to generate self-signed cert with IP SANs
    - restart service with self-signed cert
3. Add self-signed cert to Harvester
4. Add local **Minio** info as S3 into **backup-target**
5. Backup-Target Should not pop up any Error Message
6. Create Image for VM creation
7. Create VM with any resource
8. Perform VM backup
9. VM's data Should be backup into **Minio**'s folder
