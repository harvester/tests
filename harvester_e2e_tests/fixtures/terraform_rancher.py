import re
import json
import requests
from pathlib import Path
from datetime import datetime
from subprocess import run, PIPE
from dataclasses import dataclass, field

import pytest
from pkg_resources import parse_version


TF_PROVIDER = '''
terraform {
  required_providers {
    rancher2 = {
      source  = "%(provider_source)s"
      version = "%(provider_version)s"
    }
  }
}

provider "rancher2" {
  api_url   = "%(rancher_endpoint)s"
  token_key = "%(rancher_token)s"
  insecure = true
}

data "rancher2_cluster_v2" "%(harvester_name)s" {
  name = "%(harvester_name)s"
}

'''

# rancher2_machine_config_v2
TF_MACHINE_CONFIG = '''
resource "rancher2_machine_config_v2" "%(name)s" {
  generate_name = "%(name)s"
  %(harvester_config)s
}

'''
TF_HARVESTER_CONFIG = '''
  harvester_config {
    vm_namespace = "default"
    cpu_count = "2"
    memory_size = "4"
    ssh_user = "%(ssh_user)s"
    disk_info = %(disk_info)s
    network_info = %(network_info)s
    user_data = %(user_data)s
  }
'''
TF_DISK_INFO = '''<<EOF
    {
      "disks": [{
        "imageName": "%(image_name)s",
        "size": 40,
        "bootOrder": 1
      }]
    }
    EOF
'''
TF_NETWORK_INFO = '''<<EOF
    {
      "interfaces": [{
        "networkName": "%(network_name)s"
      }]
    }
    EOF
'''
TF_USER_DATA = '''<<EOF
    #cloud-config
    password: password
    chpasswd: {expire: False}
    ssh_pwauth: True
    package_update: true
    packages:
      - qemu-guest-agent
      - iptables
    runcmd:
      - - systemctl
        - enable
        - '--now'
        - qemu-guest-agent.service
    EOF
'''


# rancher2_cluster_v2
TF_CLUSTER_CONFIG = '''
resource "rancher2_cluster_v2" "%(name)s" {
  name               = "%(name)s"
  kubernetes_version = "%(rke2_version)s"
  %(rke_config)s
}

'''

TF_RKE_CONFIG = '''
  rke_config {
    %(machine_pools)s
    machine_selector_config {
      config = {
        cloud-provider-config = file("${path.module}/kubeconfig")
        cloud-provider-name = "harvester"
      }
    }
    machine_global_config = <<EOF
    cni: "calico"
    disable-kube-proxy: false
    etcd-expose-metrics: false
    EOF
    upgrade_strategy {
      control_plane_concurrency = "10%%"
      worker_concurrency        = "10%%"
    }
    etcd {
      snapshot_schedule_cron = "0 */5 * * *"
      snapshot_retention     = 5
    }
    chart_values = <<EOF
    harvester-cloud-provider:
      clusterName: %(harvester_name)s
      cloudConfigPath: /var/lib/rancher/rke2/etc/config-files/cloud-provider-config
    EOF
}
'''

TF_MACHINE_POOLS = '''
    machine_pools {
      name                         = "pool1"
      cloud_credential_secret_name = rancher2_cloud_credential.%(cloud_credential_name)s.id
      control_plane_role           = true
      etcd_role                    = true
      worker_role                  = true
      quantity                     = 1
      machine_config {
        kind = rancher2_machine_config_v2.%(machine_config_name)s.kind
        name = rancher2_machine_config_v2.%(machine_config_name)s.name
      }
    }
'''


def remove_ansicode(ctx):
    if isinstance(ctx, bytes):
        ctx = ctx.decode()
    return re.sub(r"\x1b|\[\d+m", "", ctx)


@pytest.fixture(scope="session")
def tf_script_dir(request):
    return Path(request.config.getoption('--terraform-scripts-location'))


@pytest.fixture(scope="session")
def tf_provider_version(request):
    version = request.config.getoption('--terraform-provider-rancher')
    if not version:
        import requests
        resp = requests.get("https://registry.terraform.io/v1/providers/rancher/rancher2")
        version = max(resp.json()['versions'], key=parse_version)
    return version


@pytest.fixture(scope="session")
def tf_executor(tf_script_dir):
    run(str(tf_script_dir / "terraform_install.sh"), stdout=PIPE, stderr=PIPE)
    executor = tf_script_dir / "bin/terraform"
    assert executor.is_file()

    yield executor


@pytest.fixture(scope="module")
def tf_rancher(api_client, tf_script_dir, tf_provider_version, tf_executor, harvester, rancher):
    tf_rancher = TerraformRancher(tf_executor,
                                  tf_script_dir / datetime.now().strftime("%Hh%Mm_%m-%d"))

    # kubeconfig for rancher provider
    # Ref. https://registry.terraform.io/providers/rancher/rancher2/3.1.1/docs/resources/cluster_v2
    url = f'{rancher["endpoint"]}/k8s/clusters/{harvester["id"]}/v1/harvester/kubeconfig'
    auth = (rancher["access_key"], rancher["secret_key"])
    data = {
        "clusterRoleName": "harvesterhci.io:cloudprovider",
        "namespace": "default",
        "serviceAccountName": harvester["name"]
    }
    res = requests.post(url, auth=auth, json=data, verify=False)
    kubeconfig = res.text.replace("\\n", "\n").strip('"')

    out, err, exc_code = \
        tf_rancher.initial_provider(kubeconfig, tf_provider_version, harvester, rancher)
    assert not err and 0 == exc_code
    return tf_rancher


@pytest.fixture(scope="session")
def tf_resource(tf_provider_version):
    converter = Path("./terraform_test_artifacts/json2hcl")
    return BaseTerraformResource.for_version(tf_provider_version)(converter)


class TerraformRancher:
    def __init__(self, executor, workdir):
        self.executor = executor.resolve()
        self.workdir = workdir
        self.workdir.mkdir(exist_ok=True)

    def exec_command(self, cmd, raw=False, **kws):
        rv = run(cmd, shell=True, stdout=PIPE, stderr=PIPE, cwd=self.workdir, **kws)

        if raw:
            return rv
        return remove_ansicode(rv.stdout), remove_ansicode(rv.stderr), rv.returncode

    def execute(self, cmd, raw=False, **kws):
        return self.exec_command(f"{self.executor} {cmd}", raw=raw, **kws)

    def initial_provider(self, kubeconfig, provider_version, harvester, rancher):
        kubefile = self.workdir / "kubeconfig"
        with open(kubefile, "w") as f:
            f.write(kubeconfig)

        with open(self.workdir / "provider.tf", "w") as f:
            f.write(TF_PROVIDER % {
                "provider_source": "rancher/rancher2",
                "provider_version": provider_version,
                "rancher_endpoint": rancher["endpoint"],
                "rancher_token": rancher["token"],
                "harvester_name": harvester["name"]
            })

        return self.execute("init")

    def save_as(self, content, filename, ext=".tf"):
        filepath = self.workdir / f"{filename}{ext}"
        with open(filepath, "w") as f:
            f.write(content)

    def apply_resource(self, resource_type, resource_name):
        return self.execute(f"apply -auto-approve -target {resource_type}.{resource_name}")

    def destroy_resource(self, resource_type, resource_name):
        return self.execute(f"destroy -auto-approve -target {resource_type}.{resource_name}")


@dataclass
class ResourceContext:
    type: str
    name: str
    ctx: str
    raw: dict = field(default_factory=dict, compare=False)


class BaseTerraformResource:
    #: Be used to store sub classes of BaseTerraformResource
    #: Type: Dict[Type[BaseTerraformResource], List[Type[BaseTerraformResource]]]
    _sub_classes = dict()

    #: Be used to adjust whether the class is support to specific version
    #: Type: str
    support_to = "0.0.0"

    @classmethod
    def is_support(cls, target_version):
        return parse_version(target_version) >= parse_version(cls.support_to)

    @classmethod
    def for_version(cls, version):
        for c in sorted(cls._sub_classes.get(cls, []),
                        reverse=True, key=lambda x: parse_version(x.support_to).release):
            if c.is_support(version):
                return c
        return cls

    def __init_subclass__(cls):
        for parent in cls.__mro__:
            if issubclass(parent, BaseTerraformResource):
                cls._sub_classes.setdefault(parent, []).append(cls)

    def __init__(self, converter):
        self.executor = Path(converter).resolve()

    def convert_to_hcl(self, json_spec, raw=False):
        rv = run(f"echo {json.dumps(json_spec)!r} | {self.executor!s}",
                 shell=True, stdout=PIPE, stderr=PIPE)
        if raw:
            return rv
        if rv.stderr:
            raise TypeError(rv.stderr, rv.stdout, rv.returncode)
        out = rv.stdout.decode()
        out = re.sub(r'"resource"', "resource", out)   # resource should not quote
        out = re.sub(r"\"(.+?)\" =", r"\1 =", out)     # property should not quote
        out = re.sub(r'"(data\.\S+?)"', r"\1", out)    # data should not quote
        out = re.sub(r"(.[^ ]+) = {", r"\1 {", out)    # block should not have `=`
        return out

    def make_resource(self, resource_type, resource_name, *, convert=True, **properties):
        rv = dict(resource={resource_type: {resource_name: properties}})
        if convert:
            return ResourceContext(resource_type, resource_name, self.convert_to_hcl(rv), rv)
        return rv


class TerraformResource(BaseTerraformResource):
    ''' https://github.com/rancher/terraform-provider-rancher2/tree/v3.1.1/docs/resources
    '''
    support_to = "3.1.1"

    def cloud_credential(self, name, harvester_name, *, convert=True, **properties):
        harvester_credential_config = {
            "cluster_id": f"data.rancher2_cluster_v2.{harvester_name}.cluster_v1_id",
            "cluster_type": "imported",
            "kubeconfig_content": f"data.rancher2_cluster_v2.{harvester_name}.kube_config"
        }
        return self.make_resource("rancher2_cloud_credential", name,
                                  name=name,
                                  harvester_credential_config=harvester_credential_config,
                                  convert=convert, **properties)

    def machine_config(self, rke_cluster_name, network_id, image_id, ssh_user):
        hcl_str = TF_MACHINE_CONFIG % {
            "name": rke_cluster_name,
            "harvester_config": TF_HARVESTER_CONFIG % {
                "ssh_user": ssh_user,
                "disk_info": TF_DISK_INFO % {"image_name": image_id},
                "network_info": TF_NETWORK_INFO % {"network_name": network_id},
                "user_data": TF_USER_DATA
            }
        }
        return ResourceContext("rancher2_machine_config_v2", rke_cluster_name, hcl_str, "")

    def cluster_config(self, rke_cluster_name, k8s_version, harvester_name, cloud_credential_name):
        machine_pools = TF_MACHINE_POOLS % {
            "cloud_credential_name": cloud_credential_name,
            "machine_config_name": rke_cluster_name
        }
        rke_config = TF_RKE_CONFIG % {
            "machine_pools": machine_pools,
            "harvester_name": harvester_name
        }
        hcl_str = TF_CLUSTER_CONFIG % {
            "name": rke_cluster_name,
            "rke2_version": k8s_version,
            "rke_config": rke_config
        }
        return ResourceContext("rancher2_cluster_v2", rke_cluster_name, hcl_str, "")
