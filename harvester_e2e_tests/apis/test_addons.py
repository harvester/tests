from time import sleep
from datetime import datetime, timedelta

import pytest


@pytest.mark.p0
@pytest.mark.parametrize("addon", [
    'cattle-logging-system/rancher-logging',
    'cattle-monitoring-system/rancher-monitoring',
    'harvester-system/harvester-seeder',
    'harvester-system/nvidia-driver-toolkit',
    'harvester-system/pcidevices-controller',
    'harvester-system/vm-import-controller',
])
class TestDefaultAddons:
    def test_get(self, api_client, addon):
        code, data = api_client.addons.get(addon)

        assert 200 == code, (code, data)
        assert not data.get('spec', {}).get('enabled', True), (code, data)
        assert "AddonDisabled" == data.get('status', {}).get('status')

    @pytest.mark.dependency(name="enable_addon")
    def test_enable(self, api_client, wait_timeout, addon):
        code, data = api_client.addons.enable(addon, True)

        assert 200 == code, (code, data)
        assert data.get('spec', {}).get('enabled', False), (code, data)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.addons.get(addon)
            if data.get('status', {}).get('status', "") in ("deployed", "AddonDeploySuccessful"):
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to enable addon {addon} with {wait_timeout} timed out\n"
                f"API Status({code}): {data}"
            )

    @pytest.mark.dependency(depends=["enable_addon"])
    def test_disable(self, api_client, addon, wait_timeout):
        code, data = api_client.addons.enable(addon, False)

        assert 200 == code, (code, data)
        assert not data.get('spec', {}).get('enabled', True), (code, data)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.addons.get(addon)
            if "Disabled" in data.get('status', {}).get('status', ""):
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to disable addon {addon} with {wait_timeout} timed out\n"
                f"API Status({code}): {data}"
            )
