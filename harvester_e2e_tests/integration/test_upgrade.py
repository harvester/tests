import json
import os
import re
import socket
from time import sleep
from datetime import datetime, timedelta

import pytest

from harvester_api.managers import DEFAULT_HARVESTER_NAMESPACE, DEFAULT_LONGHORN_NAMESPACE
from paramiko.ssh_exception import ChannelException, AuthenticationException, \
                                   NoValidConnectionsError

DEFAULT_STORAGE_CLS = "harvester-longhorn"

DEFAULT_USER = "ubuntu"
DEFAULT_PASSWORD = "root"

NETWORK_VLAN_ID_LABEL = "network.harvesterhci.io/vlan-id"
UPGRADE_STATE_LABEL = "harvesterhci.io/upgradeState"
CONTROL_PLANE_LABEL = "node-role.kubernetes.io/control-plane"
NODE_INTERNAL_IP_ANNOTATION = "rke2.io/internal-ip"

LOGGING_NAMESPACE = "cattle-logging-system"

expected_harvester_crds = {
    "addons.harvesterhci.io": False,
    "blockdevices.harvesterhci.io": False,
    "keypairs.harvesterhci.io": False,
    "preferences.harvesterhci.io": False,
    "settings.harvesterhci.io": False,
    "supportbundles.harvesterhci.io": False,
    "upgrades.harvesterhci.io": False,
    "versions.harvesterhci.io": False,
    "virtualmachinebackups.harvesterhci.io": False,
    "virtualmachineimages.harvesterhci.io": False,
    "virtualmachinerestores.harvesterhci.io": False,
    "virtualmachinetemplates.harvesterhci.io": False,
    "virtualmachinetemplateversions.harvesterhci.io": False,

    "clusternetworks.network.harvesterhci.io": False,
    "linkmonitors.network.harvesterhci.io": False,
    "nodenetworks.network.harvesterhci.io": False,
    "vlanconfigs.network.harvesterhci.io": False,
    "vlanstatuses.network.harvesterhci.io": False,

    "ksmtuneds.node.harvesterhci.io": False,

    "loadbalancers.loadbalancer.harvesterhci.io": False,
}

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.virtualmachines"
]

minio_manifest_fmt = """
cat <<EOF | sudo /var/lib/rancher/rke2/bin/kubectl apply \
    --kubeconfig /etc/rancher/rke2/rke2.yaml -f -
apiVersion: v1
kind: Secret
metadata:
  name: minio-secret
  namespace: default
type: Opaque
data:
  AWS_ACCESS_KEY_ID: bG9uZ2hvcm4tdGVzdC1hY2Nlc3Mta2V5
  AWS_SECRET_ACCESS_KEY: bG9uZ2hvcm4tdGVzdC1zZWNyZXQta2V5
  AWS_ENDPOINTS: aHR0cHM6Ly9taW5pby1zZXJ2aWNlLmRlZmF1bHQ6OTAwMA==
  AWS_CERT: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURMRENDQWhTZ0F3SUJBZ0lSQ\
U1kbzQycGhUZXlrMTcvYkxyWjVZRHN3RFFZSktvWklodmNOQVFFTEJRQXcKR2pFWU1CWUdBMVVFQ2\
hNUFRHOXVaMmh2Y200Z0xTQlVaWE4wTUNBWERUSXdNRFF5TnpJek1EQXhNVm9ZRHpJeApNakF3TkR\
Bek1qTXdNREV4V2pBYU1SZ3dGZ1lEVlFRS0V3OU1iMjVuYUc5eWJpQXRJRlJsYzNRd2dnRWlNQTBH\
CkNTcUdTSWIzRFFFQkFRVUFBNElCRHdBd2dnRUtBb0lCQVFEWHpVdXJnUFpEZ3pUM0RZdWFlYmdld\
3Fvd2RlQUQKODRWWWF6ZlN1USs3K21Oa2lpUVBvelVVMmZvUWFGL1BxekJiUW1lZ29hT3l5NVhqM1\
VFeG1GcmV0eDBaRjVOVgpKTi85ZWFJNWRXRk9teHhpMElPUGI2T0RpbE1qcXVEbUVPSXljdjRTaCs\
vSWo5Zk1nS0tXUDdJZGxDNUJPeThkCncwOVdkckxxaE9WY3BKamNxYjN6K3hISHd5Q05YeGhoRm9t\
b2xQVnpJbnlUUEJTZkRuSDBuS0lHUXl2bGhCMGsKVHBHSzYxc2prZnFTK3hpNTlJeHVrbHZIRXNQc\
jFXblRzYU9oaVh6N3lQSlorcTNBMWZoVzBVa1JaRFlnWnNFbQovZ05KM3JwOFhZdURna2kzZ0UrOE\
lXQWRBWHExeWhqRDdSSkI4VFNJYTV0SGpKUUtqZ0NlSG5HekFnTUJBQUdqCmF6QnBNQTRHQTFVZER\
3RUIvd1FFQXdJQ3BEQVRCZ05WSFNVRUREQUtCZ2dyQmdFRkJRY0RBVEFQQmdOVkhSTUIKQWY4RUJU\
QURBUUgvTURFR0ExVWRFUVFxTUNpQ0NXeHZZMkZzYUc5emRJSVZiV2x1YVc4dGMyVnlkbWxqWlM1a\
wpaV1poZFd4MGh3Ui9BQUFCTUEwR0NTcUdTSWIzRFFFQkN3VUFBNElCQVFDbUZMMzlNSHVZMzFhMT\
FEajRwMjVjCnFQRUM0RHZJUWozTk9kU0dWMmQrZjZzZ3pGejFXTDhWcnF2QjFCMVM2cjRKYjJQRXV\
JQkQ4NFlwVXJIT1JNU2MKd3ViTEppSEtEa0Jmb2U5QWI1cC9VakpyS0tuajM0RGx2c1cvR3AwWTZY\
c1BWaVdpVWorb1JLbUdWSTI0Q0JIdgpnK0JtVzNDeU5RR1RLajk0eE02czNBV2xHRW95YXFXUGU1e\
HllVWUzZjFBWkY5N3RDaklKUmVWbENtaENGK0JtCmFUY1RSUWN3cVdvQ3AwYmJZcHlERFlwUmxxOE\
dQbElFOW8yWjZBc05mTHJVcGFtZ3FYMmtYa2gxa3lzSlEralAKelFadHJSMG1tdHVyM0RuRW0yYmk\
0TktIQVFIcFc5TXUxNkdRakUxTmJYcVF0VEI4OGpLNzZjdEg5MzRDYWw2VgotLS0tLUVORCBDRVJU\
SUZJQ0FURS0tLS0t
  AWS_CERT_KEY: LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JSUV2UUlCQURBTkJna3Foa\
2lHOXcwQkFRRUZBQVNDQktjd2dnU2pBZ0VBQW9JQkFRRFh6VXVyZ1BaRGd6VDMKRFl1YWViZ2V3cW\
93ZGVBRDg0VllhemZTdVErNyttTmtpaVFQb3pVVTJmb1FhRi9QcXpCYlFtZWdvYU95eTVYagozVUV\
4bUZyZXR4MFpGNU5WSk4vOWVhSTVkV0ZPbXh4aTBJT1BiNk9EaWxNanF1RG1FT0l5Y3Y0U2grL0lq\
OWZNCmdLS1dQN0lkbEM1Qk95OGR3MDlXZHJMcWhPVmNwSmpjcWIzeit4SEh3eUNOWHhoaEZvbW9sU\
FZ6SW55VFBCU2YKRG5IMG5LSUdReXZsaEIwa1RwR0s2MXNqa2ZxUyt4aTU5SXh1a2x2SEVzUHIxV2\
5Uc2FPaGlYejd5UEpaK3EzQQoxZmhXMFVrUlpEWWdac0VtL2dOSjNycDhYWXVEZ2tpM2dFKzhJV0F\
kQVhxMXloakQ3UkpCOFRTSWE1dEhqSlFLCmpnQ2VIbkd6QWdNQkFBRUNnZ0VBZlVyQ1hrYTN0Q2Jm\
ZjNpcnp2cFFmZnVEbURNMzV0TmlYaDJTQVpSVW9FMFYKbSsvZ1UvdnIrN2s2eUgvdzhMOXhpZXFhQ\
TljVkZkL0JuTlIrMzI2WGc2dEpCNko2ZGZxODJZdmZOZ0VDaUFMaQpqalNGemFlQmhnT3ZsWXZHbT\
R5OTU1Q0FGdjQ1cDNac1VsMTFDRXJlL1BGbGtaWHRHeGlrWFl6NC85UTgzblhZCnM2eDdPYTgyUjd\
wT2lraWh3Q0FvVTU3Rjc4ZWFKOG1xTmkwRlF2bHlxSk9QMTFCbVp4dm54ZU11S2poQjlPTnAKTFNw\
MWpzZXk5bDZNR2pVbjBGTG53RHZkVWRiK0ZlUEkxTjdWYUNBd3hJK3JHa3JTWkhnekhWWE92VUpON\
2t2QQpqNUZPNW9uNGgvK3hXbkYzM3lxZ0VvWWZ0MFFJL2pXS2NOV1d1a2pCd1FLQmdRRGVFNlJGRU\
psT2Q1aVcxeW1qCm45RENnczVFbXFtRXN3WU95bkN3U2RhK1lNNnZVYmlac1k4WW9wMVRmVWN4cUh\
2NkFQWGpVd2NBUG1QVE9KRW8KMlJtS0xTYkhsTnc4bFNOMWJsWDBEL3Mzamc1R3VlVW9nbW5TVnhM\
a0h1OFhKR0o3VzFReEUzZG9IUHRrcTNpagpoa09QTnJpZFM0UmxqNTJwYkhscjUvQzRjUUtCZ1FEN\
HhFYmpuck1heFV2b0xxVTRvT2xiOVc5UytSUllTc0cxCmxJUmgzNzZTV0ZuTTlSdGoyMTI0M1hkaE\
4zUFBtSTNNeiswYjdyMnZSUi9LMS9Cc1JUQnlrTi9kbkVuNVUxQkEKYm90cGZIS1Jvc1FUR1hIQkE\
vM0JrNC9qOWplU3RmVXgzZ2x3eUI0L2hORy9KM1ZVV2FXeURTRm5qZFEvcGJsRwp6VWlsSVBmK1l3\
S0JnUUNwMkdYYmVJMTN5TnBJQ3psS2JqRlFncEJWUWVDQ29CVHkvUHRncUtoM3BEeVBNN1kyCnZla\
09VMWgyQVN1UkhDWHRtQXgzRndvVXNxTFFhY1FEZEw4bXdjK1Y5eERWdU02TXdwMDBjNENVQmE1L2\
d5OXoKWXdLaUgzeFFRaVJrRTZ6S1laZ3JqSkxYYXNzT1BHS2cxbEFYV1NlckRaV3R3MEEyMHNLdXQ\
0NlEwUUtCZ0hGZQpxZHZVR0ZXcjhvTDJ0dzlPcmVyZHVJVTh4RnZVZmVFdHRRTVJ2N3pjRE5qT0gx\
UnJ4Wk9aUW0ySW92dkp6MTIyCnFKMWhPUXJtV3EzTHFXTCtTU3o4L3pqMG4vWERWVUIzNElzTFR2O\
DJDVnVXN2ZPRHlTSnVDRlpnZ0VVWkxZd3oKWDJRSm4xZGRSV1Z6S3hKczVJbDNXSERqL3dXZWxnaE\
JSOGtSZEZOM0FvR0FJNldDdjJQQ1lUS1ZZNjAwOFYwbgpyTDQ3YTlPanZ0Yy81S2ZxSjFpMkpKTUg\
yQi9jbU1WRSs4M2dpODFIU1FqMWErNnBjektmQVppZWcwRk9nL015ClB6VlZRYmpKTnY0QzM5Kzdx\
SDg1WGdZTXZhcTJ0aDFEZWUvQ3NsMlM4QlV0cW5mc0VuMUYwcWhlWUJZb2RibHAKV3RUaE5oRi9oR\
VhzbkJROURyWkJKT1U9Ci0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS0K
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: longhorn-test-minio
  namespace: default
  labels:
    app: longhorn-test-minio
  finalizers:
  - forcekeeper.harvesterhci.io/v1beta1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: longhorn-test-minio
  template:
    metadata:
      labels:
        app: longhorn-test-minio
    spec:
      nodeName: {node_name}
      volumes:
      - name: minio-volume
        hostPath:
          path: /var/lib/harvester/defaultdisk/
          type: Directory
      - name: minio-certificates
        secret:
          secretName: minio-secret
          items:
          - key: AWS_CERT
            path: public.crt
          - key: AWS_CERT_KEY
            path: private.key
      containers:
      - name: minio
        image: minio/minio:RELEASE.2022-02-01T18-00-14Z
        command: ["sh", "-c", "mkdir -p /storage/backupbucket && \
mkdir -p /root/.minio/certs && \
ln -s /root/certs/private.key /root/.minio/certs/private.key && \
ln -s /root/certs/public.crt /root/.minio/certs/public.crt && \
exec minio server /storage"]
        env:
        - name: MINIO_ROOT_USER
          valueFrom:
            secretKeyRef:
              name: minio-secret
              key: AWS_ACCESS_KEY_ID
        - name: MINIO_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: minio-secret
              key: AWS_SECRET_ACCESS_KEY
        ports:
        - containerPort: 9000
        volumeMounts:
        - name: minio-volume
          mountPath: "/storage"
        - name: minio-certificates
          mountPath: "/root/certs"
          readOnly: true
---
apiVersion: v1
kind: Service
metadata:
  name: minio-service
  namespace: default
spec:
  selector:
    app: longhorn-test-minio
  ports:
    - port: 9000
      targetPort: 9000
      protocol: TCP
  sessionAffinity: ClientIP
EOF
"""

minio_cert = """
-----BEGIN CERTIFICATE-----
MIIDLDCCAhSgAwIBAgIRAMdo42phTeyk17/bLrZ5YDswDQYJKoZIhvcNAQELBQAw
GjEYMBYGA1UEChMPTG9uZ2hvcm4gLSBUZXN0MCAXDTIwMDQyNzIzMDAxMVoYDzIx
MjAwNDAzMjMwMDExWjAaMRgwFgYDVQQKEw9Mb25naG9ybiAtIFRlc3QwggEiMA0G
CSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDXzUurgPZDgzT3DYuaebgewqowdeAD
84VYazfSuQ+7+mNkiiQPozUU2foQaF/PqzBbQmegoaOyy5Xj3UExmFretx0ZF5NV
JN/9eaI5dWFOmxxi0IOPb6ODilMjquDmEOIycv4Sh+/Ij9fMgKKWP7IdlC5BOy8d
w09WdrLqhOVcpJjcqb3z+xHHwyCNXxhhFomolPVzInyTPBSfDnH0nKIGQyvlhB0k
TpGK61sjkfqS+xi59IxuklvHEsPr1WnTsaOhiXz7yPJZ+q3A1fhW0UkRZDYgZsEm
/gNJ3rp8XYuDgki3gE+8IWAdAXq1yhjD7RJB8TSIa5tHjJQKjgCeHnGzAgMBAAGj
azBpMA4GA1UdDwEB/wQEAwICpDATBgNVHSUEDDAKBggrBgEFBQcDATAPBgNVHRMB
Af8EBTADAQH/MDEGA1UdEQQqMCiCCWxvY2FsaG9zdIIVbWluaW8tc2VydmljZS5k
ZWZhdWx0hwR/AAABMA0GCSqGSIb3DQEBCwUAA4IBAQCmFL39MHuY31a11Dj4p25c
qPEC4DvIQj3NOdSGV2d+f6sgzFz1WL8VrqvB1B1S6r4Jb2PEuIBD84YpUrHORMSc
wubLJiHKDkBfoe9Ab5p/UjJrKKnj34DlvsW/Gp0Y6XsPViWiUj+oRKmGVI24CBHv
g+BmW3CyNQGTKj94xM6s3AWlGEoyaqWPe5xyeUe3f1AZF97tCjIJReVlCmhCF+Bm
aTcTRQcwqWoCp0bbYpyDDYpRlq8GPlIE9o2Z6AsNfLrUpamgqX2kXkh1kysJQ+jP
zQZtrR0mmtur3DnEm2bi4NKHAQHpW9Mu16GQjE1NbXqQtTB88jK76ctH934Cal6V
-----END CERTIFICATE-----
"""


def _lookup_image(api_client, name):
    code, data = api_client.images.get()
    if code == 200:
        for image in data['items']:
            if image['metadata']['name'] == name:
                return image
    return None


def _create_image(api_client, url, name, wait_timeout):
    image_data = _lookup_image(api_client, name)
    if image_data is None:
        code, image_data = api_client.images.create_by_url(name, url)
        assert code == 201, (
            f"failed to create image: {image_data}")

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.images.get(name)
            if 100 == data.get('status', {}).get('progress', 0):
                break
            sleep(3)
        else:
            raise AssertionError(
                "Failed to create Image with error:\n"
                f"Status({code}): {data}"
            )

    return image_data


def _get_ip_from_vmi(vmi):
    assert _check_vm_ip_assigned(vmi), "virtual machine does not have ip assigned"
    return vmi['status']['interfaces'][0]['ipAddress']


def _check_vm_is_running(vmi):
    return (vmi.get('status', {}).get('phase') == 'Running' and
            vmi.get('status', {}).get('nodeName') != "")


def _check_vm_ip_assigned(vmi):
    return (len(vmi.get('status', {}).get('interfaces')) > 0 and
            vmi.get('status').get('interfaces')[0].get('ipAddress') is not None)


def _check_assigned_ip_func(api_client, vm_name):
    def _check_assigned_ip():
        code, data = api_client.vms.get_status(vm_name)
        if code != 200:
            return False
        return _check_vm_is_running(data) and _check_vm_ip_assigned(data)
    return _check_assigned_ip


def _wait_for_vm_ready(api_client, vm_name, timeout=300):
    endtime = datetime.now() + timedelta(seconds=timeout)
    while endtime > datetime.now():
        if _check_assigned_ip_func(api_client, vm_name)():
            break
        sleep(5)
    else:
        raise AssertionError("Time out while waiting for vm to be created")


def _wait_for_write_data(vm_shell, ip, ssh_user="ubuntu", timeout=300):
    endtime = datetime.now() + timedelta(seconds=timeout)

    script = "head /dev/urandom | md5sum | head -c 20 > ~/generate_str; sync"
    while endtime > datetime.now():
        try:
            with vm_shell.login(ip, ssh_user, password=DEFAULT_PASSWORD) as sh:
                stdout, stderr = sh.exec_command(script, get_pty=True)
                assert not stderr, (
                    f"Failed to execute {script} on {ip}: {stderr}")
                return
        except (ChannelException, AuthenticationException, NoValidConnectionsError,
                socket.timeout):
            continue
    else:
        raise AssertionError(f"Time out while waiting for execute the script: {script}")


def _get_data_from_vm(vm_shell, ip, ssh_user="ubuntu", timeout=300):
    endtime = datetime.now() + timedelta(seconds=timeout)

    script = "cat ~/generate_str"
    while endtime > datetime.now():
        try:
            with vm_shell.login(ip, ssh_user, password=DEFAULT_PASSWORD) as sh:
                stdout, stderr = sh.exec_command(script, get_pty=True)
                assert not stderr, (
                    f"Failed to execute {script} on {ip}: {stderr}")
                return stdout
        except (ChannelException, AuthenticationException, NoValidConnectionsError,
                socket.timeout):
            continue
    else:
        raise AssertionError(f"Time out while waiting for execute the script: {script}")


def _ping(vm_shell, vm_ip, target_ip, ssh_user="ubuntu", timeout=300):
    endtime = datetime.now() + timedelta(seconds=timeout)

    script = f"ping -c1 {target_ip} > /dev/null && echo -n success || echo -n fail"
    while endtime > datetime.now():
        try:
            with vm_shell.login(vm_ip, ssh_user, password=DEFAULT_PASSWORD) as sh:
                stdout, stderr = sh.exec_command(script, get_pty=True)
                assert not stderr, (
                    f"Failed to execute {script} on {vm_ip}: {stderr}")
                if stdout == 'success':
                    return True
                return False
        except (ChannelException, AuthenticationException, NoValidConnectionsError,
                socket.timeout):
            continue
    else:
        raise AssertionError(f"Time out while waiting for execute the script: {script}")


def _create_basic_vm(api_client, cluster_state, vm_shell, vm_prefix, sc="",
                     timeout=300):
    reused = False
    vm_name = ""
    code, data = api_client.vms.get()
    if code == 200:
        for v in data["data"]:
            if vm_prefix in v['metadata']['name']:
                reused = True
                vm_name = v['metadata']['name']
                cluster_state.unique_id = cluster_state.unique_id[len(vm_prefix)+1:]

    if not reused:
        vm_name = f'{vm_prefix}-{cluster_state.unique_id}'

        vmspec = api_client.vms.Spec(1, 1, mgmt_network=False)

        image_id = (f"{cluster_state.ubuntu_image['metadata']['namespace']}/"
                    f"{cluster_state.ubuntu_image['metadata']['name']}")
        vmspec.add_image(cluster_state.ubuntu_image['metadata']['name'], image_id, size=5)
        vmspec.add_volume("new-sc-disk", 5, storage_cls=sc)

        network_id = (f"{cluster_state.network['metadata']['namespace']}/"
                      f"{cluster_state.network['metadata']['name']}")
        vmspec.add_network("vlan", network_id)
        vmspec.user_data = f"""#cloud-config
chpasswd:
  expire: false
package_update: true
packages:
- qemu-guest-agent
password: {DEFAULT_PASSWORD}
runcmd:
- - systemctl
  - enable
  - --now
  - qemu-guest-agent.service
ssh_pwauth: true
write_files:
  - owner: root:root
    path: /etc/netplan/50-cloud-init.yaml
    permissions: '0644'
    content: |
        network:
            version: 2
            ethernets:
                enp1s0:
                    dhcp4: yes
                    dhcp-identifier: mac
"""

        code, vm = api_client.vms.create(vm_name, vmspec)
        assert code == 201, (
            "Failed to create vm1: %s" % (data))

    _wait_for_vm_ready(api_client, vm_name, timeout=timeout)

    code, vmi = api_client.vms.get_status(vm_name)
    if code != 200:
        return None

    if not reused:
        _wait_for_write_data(vm_shell, _get_ip_from_vmi(vmi), cluster_state.image_ssh_user,
                             timeout=timeout)

    return vmi


def _create_version(request, api_client, version="master"):
    if version == "":
        version = "master"

    isoURL = request.config.getoption('--upgrade-iso-url')
    checksum = request.config.getoption('--upgrade-iso-checksum')

    return api_client.versions.create(version, isoURL, checksum)


def _get_all_nodes(api_client):
    code, data = api_client.hosts.get()
    assert code == 200, (
       f"Failed to get nodes: {code}, {data}")
    return data['data']


def _get_master_and_worker_nodes(api_client):
    nodes = _get_all_nodes(api_client)
    master_nodes = []
    worker_nodes = []
    for node in nodes:
        if node['metadata']['labels'].get(CONTROL_PLANE_LABEL) == "true":
            master_nodes.append(node)
        else:
            worker_nodes.append(node)
    return master_nodes, worker_nodes


def _is_installed_version(api_client, target_version):
    code, data = api_client.upgrades.get()
    if code == 200 and len(data['items']) > 0:
        for upgrade in data['items']:
            if upgrade.get('spec', {}).get('version') == target_version and \
               upgrade['metadata']['labels'].get(UPGRADE_STATE_LABEL) == 'Succeeded':
                return True
    return False


@pytest.fixture(scope="class")
def network(request, api_client, cluster_state):
    code, data = api_client.networks.get()
    assert code == 200, (
        "Failed to get networks: %s" % (data))

    vlan_id = request.config.getoption('--vlan-id') or 1
    for network in data['items']:
        if network['metadata']['labels'].get(NETWORK_VLAN_ID_LABEL) == f"{vlan_id}":
            cluster_state.network = network
            return

    raise AssertionError("Failed to find a routable vlan network")


@pytest.fixture(scope="class")
def unique_id(cluster_state, unique_name):
    cluster_state.unique_id = unique_name


@pytest.fixture(scope="class")
def cluster_state():
    class ClusterState:
        vm1 = None
        vm2 = None
        vm3 = None
        pass

    return ClusterState()


@pytest.fixture(scope="class")
def cluster_prereq(request, cluster_state, prepare_dependence, unique_id, network, base_sc,
                   ubuntu_image, new_sc):
    assert request.config.getoption('--upgrade-iso-url'), (
        "upgrade-iso-url must be not empty")

    assert request.config.getoption('--upgrade-iso-checksum'), (
        "upgrade-iso-checksum must be not empty")

    if request.config.getoption('--upgrade-target-version'):
        cluster_state.version_verify = True
        cluster_state.version = request.config.getoption('--upgrade-target-version')
    else:
        cluster_state.version_verify = False
        cluster_state.version = f"version-{cluster_state.unique_id}"


@pytest.fixture(scope='class')
def ubuntu_image(request, api_client, cluster_state, wait_timeout):
    image_name = "focal-server-cloudimg-amd64"

    base_url = 'https://cloud-images.ubuntu.com/focal/current/'

    cache_url = request.config.getoption('--image-cache-url')
    if cache_url:
        base_url = cache_url
    url = os.path.join(base_url, 'focal-server-cloudimg-amd64.img')

    image_json = _create_image(api_client, url, name=image_name,
                               wait_timeout=wait_timeout)
    cluster_state.ubuntu_image = image_json
    cluster_state.image_ssh_user = "ubuntu"
    return image_json


@pytest.fixture(scope="class")
def openSUSE_image(request, api_client, cluster_state, wait_timeout):
    image_name = "opensuse-leap-15-4"

    base_url = ('https://repo.opensuse.id//repositories/Cloud:/Images:'
                '/Leap_15.4/images')

    cache_url = request.config.getoption('--image-cache-url')
    if cache_url:
        base_url = cache_url
    url = os.path.join(base_url, 'openSUSE-Leap-15.4.x86_64-NoCloud.qcow2')

    image_json = _create_image(api_client, url, name=image_name,
                               timeout=wait_timeout)
    cluster_state.openSUSE_image = image_json
    cluster_state.image_ssh_user = "root"
    return image_json


def _vm1_backup(api_client, cluster_state, timeout=300):
    code, backups = api_client.backups.get()
    assert code in (200, 404), "Failed to get backups."

    backup_name = None
    for backup in backups['data']:
        if "vm1-backup" in backup['metadata']['name']:
            backup_name = backup['metadata']['name']
            break

    if backup_name is None:
        backup_name = f"vm1-backup-{cluster_state.unique_id}"
        code, data = api_client.vms.backup(cluster_state.vm1['metadata']['name'], backup_name)
        assert code == 204, (
            f"Failed to backup vm: {data}")

    def _wait_for_backup():
        nonlocal data
        code, data = api_client.backups.get(backup_name)
        assert code == 200, (
            f"Failed to get backup {backup_name}: {data}")

        return data.get('status', {}).get('readyToUse', False)

    endtime = datetime.now() + timedelta(seconds=timeout)
    while endtime > datetime.now():
        if _wait_for_backup():
            break
        sleep(5)
    else:
        raise AssertionError("Time out while waiting for backup to be created")

    return data


@pytest.fixture(scope="class")
def base_sc(request, api_client, cluster_state):
    code, data = api_client.scs.get()
    assert code == 200, (f"Failed to get storage classes: {data}")

    for sc in data['items']:
        if "base-sc" in sc['metadata']['name']:
            cluster_state.base_sc = sc
            return

    sc_name = f"base-sc-{cluster_state.unique_id}"
    cluster_state.base_sc = _create_default_storage_class(request, api_client, sc_name)


@pytest.fixture(scope="class")
def new_sc(request, api_client, cluster_state):
    code, data = api_client.scs.get()
    assert code == 200, (f"Failed to get storage classes: {data}")

    for sc in data['items']:
        if "new-sc" in sc['metadata']['name']:
            cluster_state.new_sc = sc
            return

    sc_name = f"new-sc-{cluster_state.unique_id}"
    cluster_state.new_sc = _create_default_storage_class(request, api_client, sc_name)


def _create_default_storage_class(request, api_client, name):
    replicas = request.config.getoption('--upgrade-sc-replicas') or 3

    code, data = api_client.scs.get(name)
    if code != 200:
        code, data = api_client.scs.create(name, replicas)
        assert code == 201, (
            f"Failed to create new storage class {name}: {data}")

    sc_data = data

    code, data = api_client.scs.set_default(name)
    assert code == 200, (
        f"Failed to set default storage class {name}: {data}")

    return sc_data


@pytest.fixture(scope='class')
def prepare_dependence(request, api_client, host_shell, wait_timeout):
    predep = request.config.getoption('--upgrade-prepare-dependence') or False
    if not predep:
        return

    _prepare_network(request, api_client)

    _prepare_minio(api_client, host_shell)

    _prepare_configuration(api_client, wait_timeout)


def _prepare_network(request, api_client):
    code, data = api_client.networks.get()
    assert code == 200, (
        "Failed to get networks: %s" % (data))

    vlan_id = request.config.getoption('--vlan-id') or 1
    for network in data['items']:
        if network['metadata']['labels'].get(NETWORK_VLAN_ID_LABEL) == f"{vlan_id}":
            break
    else:
        # create cluster network and network if not existing
        vlan_nic = request.config.getoption('--vlan-nic')
        assert vlan_nic is not None, "vlan nic is not configured"

        code, clusternetwork = api_client.clusternetworks.get(vlan_nic)
        assert code in {200, 404}, "Failed to get cluster network"
        if code == 404:
            code, clusternetwork = api_client.clusternetworks.create(vlan_nic)
            assert code == 201, "Failed to create cluster network"

        code, networkconfig = api_client.clusternetworks.get_config(vlan_nic)
        assert code in {200, 404}, "Failed to get network config"
        if code == 404:
            code, networkconfig = api_client.clusternetworks.create_config(vlan_nic,
                                                                           vlan_nic,
                                                                           vlan_nic)
            assert code == 201, "Failed to create network config"

        code, network = api_client.networks.create(f"vlan{vlan_id}", vlan_id,
                                                   cluster_network=vlan_nic)
        assert code == 201, "Failed to create network config"


def _prepare_minio(api_client, host_shell):
    masters, workers = _get_master_and_worker_nodes(api_client)
    assert len(masters) > 0, "Failed to get nodes"

    node_name = ""
    node_ip = ""
    for node in masters:
        if NODE_INTERNAL_IP_ANNOTATION in node["metadata"]["annotations"]:
            node_name = node["metadata"]["name"]
            node_ip = node["metadata"]["annotations"][NODE_INTERNAL_IP_ANNOTATION]
            break
    else:
        raise AssertionError("Failed to get node ip from all nodes")

    script = minio_manifest_fmt.format(node_name=node_name)

    try:
        with host_shell.login(node_ip) as shell:
            out, err = shell.exec_command(script)
        assert not err, f"Failed to create minio: f{err}"
    except Exception as e:
        raise AssertionError(f"Failed to execute command script: {e}")


def _prepare_configuration(api_client, wait_timeout):
    code, ca = api_client.settings.update("additional-ca", {"value": minio_cert})
    assert code == 200, (
        f"Failed to update ca: ${ca}")

    value = {
        "type": "s3",
        "endpoint": "https://minio-service.default:9000",
        "accessKeyId": "longhorn-test-access-key",
        "secretAccessKey": "longhorn-test-secret-key",
        "bucketName": "backupbucket",
        "bucketRegion": "us-east-1",
        "cert": "",
        "virtualHostedStyle": False,
    }
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, backup_target = api_client.settings.update("backup-target",
                                                         {"value": json.dumps(value)})
        if code == 200:
            break
        sleep(10)
    else:
        raise AssertionError(
            "Failed to update backup-target:\n"
            f"{backup_target}"
        )


@pytest.fixture(scope="class")
def vm_prereq(cluster_state, api_client, vm_shell, wait_timeout):
    # create new storage class, make it default
    # create 3 VMs:
    # - having the new storage class
    # - the VM that have some data written, take backup
    # - the VM restored from the backup
    cluster_state.vm1 = _create_basic_vm(api_client,
                                         cluster_state, vm_shell, vm_prefix="vm1",
                                         sc=cluster_state.base_sc['metadata']['name'],
                                         timeout=wait_timeout)
    cluster_state.backup = _vm1_backup(api_client, cluster_state, wait_timeout)

    code, vms = api_client.vms.get()
    assert code in (200, 404), "Failed to get vms"

    vm2_name = None
    for vm in vms['data']:
        if "vm2" in vm['metadata']['name']:
            vm2_name = vm['metadata']['name']

    if vm2_name is None:
        vm2_name = f"vm2-{cluster_state.unique_id}"
        restore_spec = api_client.backups.RestoreSpec(True, vm_name=vm2_name)
        code, data = api_client.backups.create(cluster_state.backup['metadata']['name'],
                                               restore_spec)
        assert code == 201, (
            f"Failed to restore to vm2: {data}")

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        if _check_assigned_ip_func(api_client, vm2_name)():
            break
        sleep(5)
    else:
        raise AssertionError("Time out while waiting for assigned ip for vm2")

    # modify the hostname
    code, data = api_client.vms.get(vm2_name)
    vm_spec = api_client.vms.Spec.from_dict(data)
    vm_spec.hostname = vm2_name
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.update(vm2_name, vm_spec)
        if code == 200:
            break
        sleep(5)
    else:
        raise AssertionError("Time out while waiting for update hostname")

    # restart the vm2
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.restart(vm2_name)
        if code == 204:
            break
        sleep(5)
    else:
        raise AssertionError("Time out while waiting for update hostname")

    # waiting for vm2 perform to restart
    sleep(60)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        if _check_assigned_ip_func(api_client, vm2_name)():
            break
        sleep(5)
    else:
        raise AssertionError("Time out while waiting for assigned ip for vm2")

    code, cluster_state.vm2 = api_client.vms.get_status(vm2_name)
    assert code == 200, (
        f"Failed to get vm2 vmi: {data}")

    # verify data
    vm1_data = _get_data_from_vm(vm_shell, _get_ip_from_vmi(cluster_state.vm1),
                                 cluster_state.image_ssh_user,
                                 timeout=wait_timeout)
    vm2_data = _get_data_from_vm(vm_shell, _get_ip_from_vmi(cluster_state.vm2),
                                 cluster_state.image_ssh_user,
                                 timeout=wait_timeout)

    assert vm1_data == vm2_data, ("Data in VM is lost")

    # check VMs should able to reach each others (in same networks)
    assert _ping(vm_shell, _get_ip_from_vmi(cluster_state.vm1),
                 _get_ip_from_vmi(cluster_state.vm2),
                 cluster_state.image_ssh_user,
                 timeout=wait_timeout), (
        "Failed to ping each other")

    cluster_state.vm3 = _create_basic_vm(api_client, cluster_state, vm_shell,
                                         vm_prefix="vm3",
                                         sc=cluster_state.new_sc['metadata']['name'],
                                         timeout=wait_timeout)


@pytest.mark.upgrade
@pytest.mark.negative
class TestInvalidUpgrade:
    VM_PREFIX = "vm-degraded-volume"

    def _create_vm(self, api_client, cluster_state, vm_shell, wait_timeout):
        return _create_basic_vm(api_client, cluster_state, vm_shell, self.VM_PREFIX,
                                sc=DEFAULT_STORAGE_CLS,
                                timeout=wait_timeout)

    def _degrad_volume(self, api_client, pvc_name):
        code, data = api_client.volumes.get(name=pvc_name)
        assert code == 200, (
            f"Failed to get volume {pvc_name}: {data}")

        volume = data
        volume_name = volume["spec"]["volumeName"]

        code, data = api_client.lhreplicas.get()
        assert code == 200 and len(data), (
            f"Failed to get longhorn replicas or have no replicas: {data}")

        replicas = data["items"]
        for replica in replicas:
            if replica["spec"]["volumeName"] == volume_name:
                api_client.lhreplicas.delete(name=replica["metadata"]["name"])
                break

        # wait for volume be degraded status
        sleep(10)

    def _upgrade(self, request, api_client, version):
        code, data = _create_version(request, api_client, version)
        assert code == 201, (
            f"Failed to create version {version}: {data}")

        code, data = api_client.upgrades.create(version)
        assert code == 400, (
            f"Failed to verify degraded volume: {code}, {data}")

        return data

    def _clean_degraded_volume(self, api_client, version):
        code, data = api_client.vms.delete(self.vm["metadata"]["name"])
        assert code == 200, (
            f"Failed to delete vm {self.vm['metadata']['name']}: {data}")

        code, data = api_client.versions.delete(version)
        assert code == 204, (
            f"Failed to delete version {version}: {data}")

    def test_degraded_volume(self, cluster_prereq, request, api_client, cluster_state, vm_shell,
                             wait_timeout):
        """
        Criteria: create upgrade should fails if there are any degraded volumes
        Steps:
        1. Create a VM using a volume with 3 replicas.
        2. Delete one replica of the volume. Let the volume stay in
           degraded state.
        3. Immediately upgrade Harvester.
        4. Upgrade should fail.
        """
        self.vm = self._create_vm(api_client, cluster_state, vm_shell, wait_timeout)

        claim_name = self.vm["spec"]["volumes"][0]["persistentVolumeClaim"]["claimName"]
        self._degrad_volume(api_client, claim_name)

        if cluster_state.version_verify:
            assert not _is_installed_version(api_client, cluster_state.version), (
                f"The current version is already {cluster_state.version}")
        self._upgrade(request, api_client, cluster_state.version)

        self._clean_degraded_volume(api_client, cluster_state.version)

    # TODO: waiting for https://github.com/harvester/harvester/issues/3310 to be fixed
    @pytest.mark.skip("known issue #3310")
    def test_invalid_manifest(self, api_client):
        """
        Criteria: https://github.com/harvester/tests/issues/518
        Steps:
        1. Create an invalid manifest.
        2. Try to upgrade with the invalid manifest.
        3. Upgrade should not start and fail.
        """
        # version_name = "v0.0.0"

        # code, data = api_client.versions.get(version_name)
        # if code != 200:
        #     code, data = api_client.versions.create(version_name, "https://invalid_version_url")
        #     assert code == 201, (
        #         "Failed to create invalid version: %s", data)

        # code, data = api_client.upgrades.create(version_name)
        # assert code == 201, (
        #     "Failed to create invalid upgrade: %s", data)


@pytest.mark.upgrade
@pytest.mark.any_nodes
class TestAnyNodesUpgrade:

    @pytest.mark.dependency(name="any_nodes_upgrade")
    def test_perform_upgrade(self, cluster_prereq, vm_prereq, request, api_client, cluster_state,
                             wait_timeout):
        """
        - perform upgrade
        - check all nodes upgraded
        """
        if cluster_state.version_verify:
            assert not _is_installed_version(api_client, cluster_state.version), (
                f"The current version is already {cluster_state.version}")

        self._perform_upgrade(request, api_client, cluster_state)

        # start vms when are stopped
        code, data = api_client.vms.get()
        assert code == 200, (f"Failed to get vms: {data}")

        for vm in data["data"]:
            if "ready" not in vm["status"] or not vm["status"]["ready"]:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    code, data = api_client.vms.start(vm["metadata"]["name"])
                    if code == 204:
                        break
                    sleep(5)
                else:
                    raise AssertionError(f"start vm timeout: {data}")

                # wait for vm to be assigned an IP
                _wait_for_vm_ready(api_client, vm["metadata"]["name"],
                                   timeout=wait_timeout)

    def _perform_upgrade(self, request, api_client, cluster_state):
        # force create upgrade version
        code, data = api_client.versions.get(cluster_state.version)
        if code == 200:
            code, data = api_client.versions.delete(cluster_state.version)
            assert code == 204, (
                f"Failed to delete version {cluster_state.version}: {data}")

        code, data = _create_version(request, api_client, cluster_state.version)
        assert code == 201, (
            f"Failed to create version {cluster_state.version}: {data}")

        code, data = api_client.upgrades.create(cluster_state.version)
        assert code == 201, (
            f"Failed to upgrade version {cluster_state.version}: {code}, {data}")

        def _wait_for_upgrade():
            try:
                code, upgrade_data = api_client.upgrades.get(data["metadata"]["name"])
                if code != 200:
                    return False, {}
            except Exception:
                return False, upgrade_data.get('status', {})

            status = upgrade_data.get('status', {})

            if upgrade_data['metadata'].get('labels', {}).get(UPGRADE_STATE_LABEL) == "Succeeded":
                return True, status

            conds = upgrade_data.get('status', {}).get('conditions', [])
            if len(conds) > 0:
                for cond in conds:
                    if cond["status"] == "False":
                        cond_type = cond["type"]
                        raise AssertionError(f"Upgrade failed: {cond_type}: {cond}")

                    if cond["type"] == "Completed" and cond["status"] == "True":
                        return True, status

            return False, status

        nodes = _get_all_nodes(api_client)
        upgrade_timeout = request.config.getoption('--upgrade-wait-timeout') or 7200
        endtime = datetime.now() + timedelta(seconds=upgrade_timeout * len(nodes))
        while endtime > datetime.now():
            upgraded, status = _wait_for_upgrade()
            if upgraded:
                break
            sleep(5)
        else:
            raise AssertionError(f"Upgrade timeout: {status}")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_logging_pods(self, api_client):
        """ Verify logging pods and logs
        Criteria: https://github.com/harvester/tests/issues/535
        """

        code, pods = api_client.get_pods(namespace=LOGGING_NAMESPACE)
        assert code == 200 and len(pods['data']) > 0, "No logging pods found"

        fails = []
        for pod in pods['data']:
            # Verify pod is running or completed
            phase = pod["status"]["phase"]
            if phase not in ("Running", "Succeeded"):
                fails.append((pod['metadata']['name'], phase))
        else:
            assert not fails, (
                "\n".join(f"Pod({n})'s phase({p}) is not expected." for n, p in fails)
            )

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_audit_log(self, api_client, host_shell, wait_timeout):
        masters, workers = _get_master_and_worker_nodes(api_client)
        assert len(masters) > 0, "No master nodes found"

        script = ("sudo tail /var/lib/rancher/rke2/server/logs/audit.log | awk 'END{print}' "
                  "| jq .requestReceivedTimestamp "
                  "| xargs -I {} date -d \"{}\" +%s")

        node_ips = [n["metadata"]["annotations"][NODE_INTERNAL_IP_ANNOTATION] for n in masters]
        cmp = dict()
        done = set()
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            for ip in done.symmetric_difference(node_ips):
                try:
                    with host_shell.login(ip) as shell:
                        out, err = shell.exec_command(script)
                        timestamp = int(out)
                        if not err and ip not in cmp:
                            cmp[ip] = timestamp
                            continue
                        if not err and cmp[ip] < timestamp:
                            done.add(ip)
                except (ChannelException, AuthenticationException, NoValidConnectionsError,
                        socket.timeout):
                    continue

            if not done.symmetric_difference(node_ips):
                break
            sleep(5)
        else:
            raise AssertionError(
                "\n".join("Node {ip} audit log is not updated." for ip in set(node_ips) ^ done)
            )

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_network(self, api_client, cluster_state):
        """ Verify cluster and VLAN networks
        - cluster network `mgmt` should exists
        - Created VLAN should exists
        """

        code, cnets = api_client.clusternetworks.get()
        assert code == 200, (
            "Failed to get Networks: %d, %s" % (code, cnets))

        assert len(cnets["items"]) > 0, ("No Networks found")

        assert any(n['metadata']['name'] == "mgmt" for n in cnets['items']), (
            "Cluster network mgmt not found")

        code, vnets = api_client.networks.get()
        assert code == 200, (f"Failed to get VLANs: {code}, {vnets}" % (code, vnets))
        assert len(vnets["items"]) > 0, ("No VLANs found")

        used_vlan = cluster_state.network['metadata']['name']
        assert any(used_vlan == n['metadata']['name'] for n in vnets['items']), (
            f"VLAN {used_vlan} not found")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_vms(self, api_client, cluster_state, vm_shell, wait_timeout):
        """ Verify VMs' state and data
        Criteria:
        - VMs should keep in running state
        - data in VMs should not lost
        """

        code, vmis = api_client.vms.get_status()
        assert code == 200, (
            f"Failed to get VMs: {code}, {vmis}")

        assert len(vmis["data"]) > 0, ("No VMs found")

        fails = []
        for vmi in vmis['data']:
            if "vm1" in vmi['metadata']['name']:
                cluster_state.vm1 = vmi
            if "vm2" in vmi['metadata']['name']:
                cluster_state.vm2 = vmi
            if not _check_vm_is_running(vmi):
                fails.append(vmi['metadata']['name'])
        assert not fails, "\n".join(f"VM {n} is not running" for n in fails)

        vm1_data = _get_data_from_vm(vm_shell, _get_ip_from_vmi(cluster_state.vm1),
                                     cluster_state.image_ssh_user,
                                     timeout=wait_timeout)
        vm2_data = _get_data_from_vm(vm_shell, _get_ip_from_vmi(cluster_state.vm2),
                                     cluster_state.image_ssh_user,
                                     timeout=wait_timeout)
        assert vm1_data == vm2_data, ("Data in VM is lost")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_restore_vm(self, api_client, cluster_state, vm_shell, wait_timeout):
        """ Verify VM restored from the backup
        Criteria:
        - VM should able to start
        - data in VM should not lost
        """

        vm4_name = f"vm4-{cluster_state.unique_id}"
        restore_spec = api_client.backups.RestoreSpec(True, vm_name=vm4_name)
        code, data = api_client.backups.create(cluster_state.backup['metadata']['name'],
                                               restore_spec)
        assert code == 201, (
            f"Failed to restore to vm4: {data}")

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            if _check_assigned_ip_func(api_client, vm4_name)():
                break
            sleep(5)
        else:
            raise AssertionError("Time out while waiting for assigned ip for vm4")

        code, vm4 = api_client.vms.get_status(vm4_name)
        assert code == 200, (
            f"Failed to get vm2 vmi: {vm4}")

        vm4_data = _get_data_from_vm(vm_shell, _get_ip_from_vmi(vm4),
                                     cluster_state.image_ssh_user,
                                     timeout=wait_timeout)
        vm1_data = _get_data_from_vm(vm_shell, _get_ip_from_vmi(cluster_state.vm1),
                                     cluster_state.image_ssh_user,
                                     timeout=wait_timeout)
        assert vm1_data == vm4_data, ("Data in VM is not the same as the original")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_storage_class(self, api_client):
        """ Verify StorageClasses and defaults
        - `new_sc` should be settle as default
        - `longhorn` should exists
        """
        code, scs = api_client.scs.get()
        assert code == 200, (
            "Failed to get StorageClasses: %d, %s" % (code, scs))

        assert len(scs["items"]) > 0, ("No StorageClasses found")

        longhorn_exists = False
        test_exists = False
        test_default = False
        for sc in scs["items"]:
            annotations = sc["metadata"].get('annotations', {})
            if sc["metadata"]["name"] == "longhorn":
                longhorn_exists = True

            if "new-sc" in sc["metadata"]["name"]:
                test_exists = True
                default = annotations["storageclass.kubernetes.io/is-default-class"]
                if default == "true":
                    test_default = True

        assert longhorn_exists, ("longhorn StorageClass not found")
        assert test_exists, ("test StorageClass not found")
        assert test_default, ("test StorageClass is not default")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_os_version(self, request, api_client, cluster_state, host_shell):
        # Verify /etc/os-release on all nodes
        script = "cat /etc/os-release"
        if not cluster_state.version_verify:
            pytest.skip("skip verify os version")

        # Get all nodes
        nodes = _get_all_nodes(api_client)
        for node in nodes:
            node_ip = node["metadata"]["annotations"][NODE_INTERNAL_IP_ANNOTATION]

            with host_shell.login(node_ip) as sh:
                lines, stderr = sh.exec_command(script, get_pty=True, splitlines=True)
                assert not stderr, (
                    f"Failed to execute {script} on {node_ip}: {stderr}")

                # eg: PRETTY_NAME="Harvester v1.1.0"
                assert cluster_state.version == re.findall(r"Harvester (.+?)\"", lines[3])[0], (
                    "OS version is not correct")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_rke2_version(self, api_client, host_shell):
        # Verify node version on all nodes
        script = "cat /etc/harvester-release.yaml"

        # Verify rke2 version
        except_rke2_version = ""
        masters, workers = _get_master_and_worker_nodes(api_client)
        for node in masters:
            node_ip = node["metadata"]["annotations"][NODE_INTERNAL_IP_ANNOTATION]

            # Get except rke2 version
            if except_rke2_version == "":
                with host_shell.login(node_ip) as sh:
                    lines, stderr = sh.exec_command(script, get_pty=True, splitlines=True)
                    assert not stderr, (
                        f"Failed to execute {script} on {node_ip}: {stderr}")

                    for line in lines:
                        if "kubernetes" in line:
                            except_rke2_version = re.findall(r"kubernetes: (.*)", line.strip())[0]
                            break

                    assert except_rke2_version != "", ("Failed to get except rke2 version")

            assert node.get('status', {}).get('nodeInfo', {}).get(
                   "kubeletVersion", "") == except_rke2_version, (
                   "rke2 version is not correct")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_deployed_components_version(self, api_client):
        """ Verify deployed kubevirt and longhorn version
        Criteria:
        - except version(get from apps.catalog.cattle.io/harvester) should be equal to the version
          of kubevirt and longhorn
        """

        kubevirt_version_existed = False
        engine_image_version_existed = False
        longhorn_manager_version_existed = False

        # Get except version from apps.catalog.cattle.io/harvester
        code, apps = api_client.get_apps_catalog(name="harvester",
                                                 namespace=DEFAULT_HARVESTER_NAMESPACE)
        assert code == 200 and apps['type'] != "error", (
            f"Failed to get apps.catalog.cattle.io/harvester: {apps['message']}")

        # Get except image of kubevirt and longhorn
        kubevirt_operator = (
            apps['spec']['chart']['values']['kubevirt-operator']['containers']['operator'])
        kubevirt_operator_image = (
            f"{kubevirt_operator['image']['repository']}:{kubevirt_operator['image']['tag']}")

        longhorn = apps['spec']['chart']['values']['longhorn']['image']['longhorn']
        longhorn_images = {
            "engine-image": f"{longhorn['engine']['repository']}:{longhorn['engine']['tag']}",
            "longhorn-manager": f"{longhorn['manager']['repository']}:{longhorn['manager']['tag']}"
        }

        # Verify kubevirt version
        code, pods = api_client.get_pods(namespace=DEFAULT_HARVESTER_NAMESPACE)
        assert code == 200 and len(pods['data']) > 0, (
            f"Failed to get pods in namespace {DEFAULT_HARVESTER_NAMESPACE}")

        for pod in pods['data']:
            if "virt-operator" in pod['metadata']['name']:
                kubevirt_version_existed = (
                    kubevirt_operator_image == pod['spec']['containers'][0]['image'])

        # Verify longhorn version
        code, pods = api_client.get_pods(namespace=DEFAULT_LONGHORN_NAMESPACE)
        assert code == 200 and len(pods['data']) > 0, (
            f"Failed to get pods in namespace {DEFAULT_LONGHORN_NAMESPACE}")

        for pod in pods['data']:
            if "longhorn-manager" in pod['metadata']['name']:
                longhorn_manager_version_existed = (
                  longhorn_images["longhorn-manager"] == pod['spec']['containers'][0]['image'])
            elif "engine-image" in pod['metadata']['name']:
                engine_image_version_existed = (
                    longhorn_images["engine-image"] == pod['spec']['containers'][0]['image'])

        assert kubevirt_version_existed, "kubevirt version is not correct"
        assert engine_image_version_existed, "longhorn engine image version is not correct"
        assert longhorn_manager_version_existed, "longhorn manager version is not correct"

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_crds_existed(self, api_client):
        """ Verify crds existed
        Criteria:
        - crds should be existed
        """
        not_existed_crds = []
        exist_crds = True
        for crd in expected_harvester_crds:
            code, _ = api_client.get_crds(name=crd)

            if code != 200:
                exist_crds = False
                not_existed_crds.append(crd)

        if not exist_crds:
            raise AssertionError(f"CRDs {not_existed_crds} are not existed")
