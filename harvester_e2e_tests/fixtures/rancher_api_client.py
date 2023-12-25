import warnings

import pytest
from pkg_resources import parse_version

from rancher_api import RancherAPI


@pytest.fixture(scope="session")
def rancher_api_client(request):
    endpoint = request.config.getoption("--rancher-endpoint")
    password = request.config.getoption("--rancher-admin-password")
    ssl_verify = request.config.getoption("--ssl_verify", False)

    api = RancherAPI(endpoint)
    api.authenticate("admin", password, verify=ssl_verify)

    api.session.verify = ssl_verify

    return api


@pytest.fixture(scope="session")
def k8s_version(request, api_client, rancher_api_client):
    harv_version = api_client.hosts.get()[1][0]['status']['nodeInfo']['kubeletVersion']
    rke2_version = (request.config.getoption("--RKE2-version")
                    or harv_version)

    # Ref: https://github.com/rancher/dashboard/blob/master/shell/edit/provisioning.cattle.io.cluster/rke2.vue  # noqa
    releases = rancher_api_client._get("v1-rke2-release/releases").json()['data']
    supports = sorted([r['id'] for r in releases], key=parse_version)

    if parse_version(rke2_version) > parse_version(supports[-1]):
        warnings.warn(UserWarning(
            f"The RKE version is not support by the Rancher (too new), use latest `{supports[-1]}`"
            ))
        return supports[-1]
    elif parse_version(rke2_version) < parse_version(supports[0]):
        warnings.warn(UserWarning(
            f"The RKE version is not support by the Rancher (too old), use latest `{supports[0]}`"
            ))
        return supports[0]
    elif parse_version(harv_version) > parse_version(rke2_version):
        warnings.warn(UserWarning("Target RKE version is old than current Harvester using"))
        return rke2_version
    else:
        return rke2_version
