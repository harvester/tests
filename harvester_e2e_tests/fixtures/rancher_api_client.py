import pytest

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
