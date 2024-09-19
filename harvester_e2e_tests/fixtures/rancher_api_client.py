import warnings

import pytest
from pkg_resources import parse_version

from rancher_api import RancherAPI


@pytest.fixture(scope="session")
def rancher_api_client(request, harvester_metadata):
    endpoint = request.config.getoption("--rancher-endpoint")
    password = request.config.getoption("--rancher-admin-password")
    ssl_verify = request.config.getoption("--ssl_verify", False)

    api = RancherAPI(endpoint)
    api.authenticate("admin", password, verify=ssl_verify)

    api.session.verify = ssl_verify

    harvester_metadata['Rancher Endpoint'] = endpoint
    harvester_metadata['Rancher Version'] = api.cluster_version.raw

    return api


def _pickup_k8s_version(versions, target_version):
    """
    versions: list of str, e.g. ['v1.26.16-rancher2-3', 'v1.25.15-rancher1-1', ...]
    target_version: str, e.g. 'v1.26', 'v1.26.16', ...
    """
    # e.g. v1.26.16-rancher2-3 / v1.26.16+rke2r1 will be sort as v1.26.16
    sorted_vers = sorted(versions,
                         key=lambda v: parse_version(v.split("+")[0].split("-")[0]),
                         reverse=True)

    for ver in sorted_vers:
        if ver.startswith(target_version):
            warnings.warn(UserWarning(f"Adopt {ver} for target k8s-version {target_version}"))
            return ver

    raise AssertionError(
        f"No supported version fits target k8s-version {target_version}\n"
        f"Rancher endpoint supports {versions}"
    )


@pytest.fixture(scope='session')
def rke1_version(request, rancher_api_client, harvester_metadata):
    target_ver = request.config.getoption("--k8s-version")

    code, data = rancher_api_client.settings.get("k8s-versions-current")
    assert 200 == code, (code, data)
    supported_vers = data["value"].split(",")

    ver = _pickup_k8s_version(supported_vers, target_ver)
    harvester_metadata['RKE1 Version'] = ver
    return ver


@pytest.fixture(scope="session")
def rke2_version(request, rancher_api_client, harvester_metadata):
    target_ver = request.config.getoption("--k8s-version")

    # Ref. https://github.com/rancher/dashboard/blob/master/shell/edit/provisioning.cattle.io.cluster/rke2.vue  # noqa
    resp = rancher_api_client._get("v1-rke2-release/releases")
    assert resp.ok
    supported_vers = [r['id'] for r in resp.json()['data']]

    ver = _pickup_k8s_version(supported_vers, target_ver)
    harvester_metadata['RKE2 Version'] = ver
    return ver


@pytest.fixture(scope="session")
def k3s_version(request, rancher_api_client, harvester_metadata):
    target_ver = request.config.getoption("--k8s-version")

    resp = rancher_api_client._get("v1-k3s-release/releases")
    assert resp.ok
    supported_vers = [r['id'] for r in resp.json()['data']]

    ver = _pickup_k8s_version(supported_vers, target_ver)
    harvester_metadata['K3S Version'] = ver
    return ver
