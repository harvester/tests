import re
import json
from pathlib import Path
from datetime import datetime
from subprocess import run, PIPE

import pytest

TF_PROVIDER = '''
terraform {{
  required_version = "{tf_version}"
  required_providers {{
    harvester = {{
      source  = "{provider_source}"
      version = "{provider_version}"
    }}
  }}
}}

provider "harvester" {{
    kubeconfig = "{config_path}"
}}
'''


def remove_ansicode(ctx):
    if isinstance(ctx, bytes):
        ctx = ctx.decode()
    return re.sub(r"\x1b|\[\d+m", "", ctx)


@pytest.fixture(scope="session")
def tf_provider_version(request):
    version = request.config.getoption('--terraform-provider-harvester')
    if not version:
        import requests
        return requests.get(
            "https://api.github.com/repos/harvester/terraform-provider-harvester/releases/latest"
        ).json()['name'].lstrip('v')
    return version


@pytest.fixture(scope="session")
def tf_executor(request):
    path = Path(request.config.getoption('--terraform-scripts-location'))
    run(path / "terraform_install.sh", stdout=PIPE, stderr=PIPE)
    executor = path / "bin/terraform"
    assert executor.is_file()

    yield executor


@pytest.fixture(scope="session")
def tf_harvester(request, api_client, tf_executor, tf_provider_version):
    class TerraformHarvester:
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
            return self.exec_command(f"{self.executor} {cmd}")

        def initial_provider(self, kubeconfig, provider_version):
            kubefile = self.workdir / ".kube"
            with open(kubefile, "w") as f:
                f.write(kubeconfig)

            with open(self.workdir / "provider.tf", "w") as f:
                f.write(TF_PROVIDER.format(
                    tf_version=">=0.13", config_path=kubefile.resolve(),
                    provider_source="harvester/harvester", provider_version=provider_version
                ))

            return self.execute("init")

        def save_as(self, content, filename, ext=".tf"):
            filepath = self.workdir / f"{filename}{ext}"
            with open(filepath, "w") as f:
                f.write(content)

        def apply_resource(self, resource_type, resource_name):
            return self.execute(f"apply -auto-approve -target {resource_type}.{resource_name}")

        def destroy_resource(self, resource_type, resource_name):
            return self.execute(f"destroy -auto-approve -target {resource_type}.{resource_name}")

    path = Path(request.config.getoption('--terraform-scripts-location'))
    harv = TerraformHarvester(tf_executor, path / datetime.now().strftime("%Hh%Mm_%m-%d"))
    kuebconfig = api_client.generate_kubeconfig()
    out, err, exc_code = harv.initial_provider(kuebconfig, tf_provider_version)
    assert 0 == exc_code and not err

    return harv


@pytest.fixture(scope="session")
def tf_resource(request, tf_provider_version):
    from dataclasses import dataclass

    @dataclass
    class ResourceContext:
        type: str
        name: str
        ctx: str

    class TerraformResource:
        @classmethod
        def _support_version(cls, version):
            return True

        @classmethod
        def from_version(cls, version):
            for c in cls.__subclasses__():
                if c._support_version(version):
                    return c()
            return cls()

        def __init__(self):
            self.executor = Path("./terraform_test_artifacts/json2hcl").resolve()

        def convert_to_hcl(self, json_spec, raw=False):
            rv = run(f"echo {json.dumps(json_spec)!r} | {self.executor!s}",
                     shell=True, stdout=PIPE, stderr=PIPE)
            if raw:
                return rv
            if rv.stderr:
                raise TypeError(rv.stderr, rv.stdout, rv.returncode)
            out = rv.stdout.decode()
            out = re.sub(r'"resource"', "resource", out)  # resource should not quote
            out = re.sub(r"\"(.+?)\" =", r"\1 =", out)  # property should not quote
            return out

        def ssh_key(self, resource_name, name, public_key, *, convert=True, **kwargs):
            spec = {"name": name, "public_key": public_key}
            spec.update(kwargs)
            rv = dict(resource=dict(harvester_ssh_key={resource_name: spec}))

            if convert:
                return ResourceContext("harvester_ssh_key", resource_name, self.convert_to_hcl(rv))
            return rv

        def storage_class(
            self, resource_name, name, replicas=1, stale_timeout=30, migratable="true",
            *, convert=True, **kwargs
        ):
            spec = {
                "name": name,
                "parameters": {
                    "migratable": migratable,
                    "numberOfReplicas": str(replicas),
                    "staleReplicaTimeout": str(stale_timeout)
                }
            }
            other_params = kwargs.pop('parameters', {})
            spec.update(kwargs)
            spec['parameters'].update(other_params)
            rv = dict(resource=dict(harvester_storageclass={resource_name: spec}))

            if convert:
                return ResourceContext(
                    "harvester_storageclass", resource_name, self.convert_to_hcl(rv)
                )
            return rv

        def volume(self, resource_name, name, size, *, convert=True, **kwargs):
            spec = {
                "name": name,
                "size": size if isinstance(size, str) else f"{size}Gi"
            }
            spec.update(kwargs)
            rv = dict(resource=dict(harvester_volume={resource_name: spec}))

            if convert:
                return ResourceContext("harvester_volume", resource_name, self.convert_to_hcl(rv))
            return rv

    return TerraformResource.from_version(tf_provider_version)
