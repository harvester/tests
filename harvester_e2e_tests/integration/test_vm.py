from datetime import datetime, timedelta
from time import sleep

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]


@pytest.mark.singlevmtest
@pytest.mark.virtual_machines_p1
class TestVmMigrate:
    @pytest.mark.dependency()
    def test_prerequisite(self, api_client):
        status_code, nodes_info = api_client.hosts.get()

        assert status_code == 200, f"Failed to list nodes with error: {nodes_info}"
        assert len(nodes_info['data']) > 1, "Please use multiple hosts to test vm migration"

    @pytest.mark.dependency(depends=["TestVmMigrate::test_prerequisite"])
    def test_create_vm(self, api_client, unique_name, focal_image, wait_timeout):
        vmSpec = api_client.vms.Spec(1, 1)
        vmSpec.add_image('disk-0', focal_image)
        code, data = api_client.vms.create(unique_name, vmSpec)
        assert code == 201, (
            f"Failed to create VM {unique_name} with error: {code}, {data}"
        )

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(unique_name)
            if data.get('status', {}).get('ready', False):
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Can't find VM {unique_name} with {wait_timeout} timed out\n"
                f"Got error: {code}, {data}"
            )
        sleep(10)

    @pytest.mark.dependency(depends=["TestVmMigrate::test_create_vm"])
    def test_migrate(self, api_client, unique_name, wait_timeout):
        _, nodes_info = api_client.hosts.get()
        code, vmi_data = api_client.vmis.get(unique_name)
        assert code == 200, (
            f"Can't get VMI {unique_name} with error: {code}, {vmi_data}"
        )

        src_host = vmi_data['status']['nodeName']
        dst_host = ""
        for node_data in nodes_info['data']:
            if node_data['metadata']['name'] != src_host:
                dst_host = node_data['metadata']['name']

        code, data = api_client.vms.migrate(unique_name, dst_host)
        assert code == 204, (
            f"Can't migrate VM {unique_name} from host {src_host} to {dst_host}"
        )

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vmis.get(unique_name)
            if data.get('status', {}).get('migrationState', {}).get('completed', False):
                break
            sleep(5)
        else:
            raise AssertionError(
                f"The migration of VM {unique_name} is not completed with {wait_timeout} timed out"
                f"Got error: {code}, {data}"
            )

        # teardown
        api_client.vms.delete(unique_name)
