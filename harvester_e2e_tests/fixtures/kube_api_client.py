# Copyright (c) 2024 SUSE LLC
#
# pylint: disable=missing-function-docstring

import pytest

from kube_api import KubeAPI


@pytest.fixture(scope="session")
def kube_api_client(request):
    endpoint = request.config.getoption("--endpoint")
    username = request.config.getoption("--username")
    password = request.config.getoption("--password")
    tls_verify = request.config.getoption("--ssl_verify", False)

    with KubeAPI(endpoint, tls_verify) as api:
        api.authenticate(username, password, verify=tls_verify)

        yield api.get_client()
