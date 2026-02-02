# Copyright (c) 2024 SUSE LLC
#
# pylint: disable=missing-function-docstring, redefined-outer-name

from urllib.parse import urljoin

import kubernetes
import pytest
import requests
import semver
import yaml


pytest_plugins = [
    "harvester_e2e_tests.fixtures.kube_api_client",
    "harvester_e2e_tests.fixtures.api_client"
]


@pytest.fixture(scope="session")
def server_version(api_client):
    code, data = api_client.settings.get(name="server-version")
    assert code == 200
    assert data.get("value") is not None

    yield semver.VersionInfo.parse(data.get("value").lstrip("v"))


@pytest.fixture(scope="module", params=[
    ("csi-snapshotter", "volumesnapshotclasses"),
    ("csi-snapshotter", "volumesnapshotcontents"),
    ("csi-snapshotter", "volumesnapshots"),
    ("kubevirt-operator", "crd-kubevirt"),
    ("whereabouts", "whereabouts.cni.cncf.io_ippools"),
    ("whereabouts", "whereabouts.cni.cncf.io_overlappingrangeipreservations")
])
def chart_and_file_name(request):
    yield request.param


@pytest.fixture(scope="module")
def expected_crd(server_version, chart_and_file_name):
    raw_url = "https://raw.githubusercontent.com/harvester/harvester/"
    raw_url = urljoin(raw_url, f"v{server_version.major}.{server_version.minor}/")
    raw_url = urljoin(raw_url, "deploy/charts/harvester/dependency_charts/")
    raw_url = urljoin(raw_url, f"{chart_and_file_name[0]}/")
    raw_url = urljoin(raw_url, "crds/")
    raw_url = urljoin(raw_url, f"{chart_and_file_name[1]}.yaml")

    resp = requests.get(raw_url, allow_redirects=True)
    cont = resp.content.decode("utf-8")
    data = yaml.safe_load(cont)
    yield data


@pytest.fixture(scope="module")
def actual_crd(kube_api_client, expected_crd):
    name = expected_crd['metadata']['name']
    kube_client = kubernetes.client.ApiextensionsV1Api(kube_api_client)
    yield kube_client.read_custom_resource_definition(name=name)


@pytest.mark.api
def test_api_version(expected_crd, actual_crd):
    expected_versions = []
    for ver in expected_crd['spec']['versions']:
        expected_versions.append(ver['name'])

    actual_versions = []
    for ver in actual_crd.spec.versions:
        actual_versions.append(ver.name)

    assert expected_crd['metadata']['name'] == actual_crd.metadata.name

    # Make sure all expected versions are there
    for ver in expected_versions:
        assert ver in actual_versions

    # Make sure all installed versions are expected
    for ver in actual_versions:
        assert ver in expected_versions
