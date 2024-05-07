import pytest

pytest_plugins = [
   "harvester_e2e_tests.fixtures.api_client"
  ]


@pytest.mark.p0
@pytest.mark.negative
@pytest.mark.virtualmachines
class TestVMNegative:
    def test_get_not_exist(self, api_client, unique_name):
        """
        1. Tries to get a VM that doesn't exist
        2. Checks that the get command gets a 404
        """
        code, data = api_client.vms.get(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get('code'), (code, data)

    def test_delete_not_exist(self, api_client, unique_name):
        """ ref: https://github.com/harvester/tests/issues/1215
        1. Tries to delete a VM that doesn't exist
        2. Checks that it gets a 404
        """
        try:
            api_client.set_retries(1)
            code, data = api_client.vms.delete(unique_name)
            assert 404 == code, (code, data)
            assert "NotFound" in data.get('code'), (code, data)
        finally:
            api_client.set_retries()
