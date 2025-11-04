from time import sleep
from datetime import datetime, timedelta

import pytest


pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]


@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.namespaces
class TestNamespaces:
    @pytest.mark.negative
    def test_get_not_exist(self, api_client, unique_name):
        code, data = api_client.namespaces.get(unique_name)
        assert code == 404
        assert "NotFound" == data.get("code")

    @pytest.mark.negative
    def test_delete_not_exist(self, api_client, unique_name):
        code, data = api_client.namespaces.delete(unique_name)
        assert code == 404
        assert "NotFound" == data.get("code")

    def test_get_defaults(self, api_client):
        for name in ('default', 'harvester-public'):
            status_code, data = api_client.namespaces.get(name)
            assert status_code == 200, (
                f"Unable to get default namespace: {name}\n"
                f"Response: {data}"
            )

    @pytest.mark.dependency(name="create_namespaces")
    def test_create(self, api_client, unique_name):
        status_code, data = api_client.namespaces.create(unique_name)

        assert status_code == 201, (
            f"Unable to create Namespace `{unique_name}`\n"
            f"Response: {data}"
        )

    @pytest.mark.dependency(depends=["create_namespaces"])
    def test_get(self, api_client, unique_name):
        # Case 1: get all namespaces
        status_code, data = api_client.namespaces.get()

        assert len(data['data']) > 2, (status_code, data)

        # Case 2: get created namespaces
        status_code, data = api_client.namespaces.get(unique_name)

        assert status_code == 200
        assert unique_name == data['metadata'].get('name')

    @pytest.mark.dependency(depends=["create_namespaces"])
    def test_delete(self, api_client, unique_name):
        status_code, data = api_client.namespaces.delete(unique_name)

        assert 200 == status_code, (status_code, data)
        assert "Terminating" == data['status']['phase']

        # 3 mins for cluster to validate keypair
        endtime = datetime.now() + timedelta(minutes=3)
        while endtime > datetime.now():
            status_code, data = api_client.namespaces.get(unique_name)
            if 404 == status_code:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"The namespace {unique_name} still not be deleted after 3 mins"
            )
