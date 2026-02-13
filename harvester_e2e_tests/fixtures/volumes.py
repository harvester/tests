
import pytest
from .base import wait_until
from datetime import datetime, timedelta
from time import sleep

pytest_plugins = ["harvester_e2e_tests.fixtures.api_client"]


@pytest.fixture(scope="session")
def volume_checker(api_client, wait_timeout, sleep_timeout):
    class VolumeChecker:
        def __init__(self):
            self.volumes = api_client.volumes
            self.lhvolumes = api_client.lhvolumes

        @wait_until(wait_timeout, sleep_timeout)
        def wait_volumes_detached(self, vol_names):
            for vol_name in vol_names:
                code, data = self.volumes.get(name=vol_name)
                if not (code == 200):
                    return False, (code, data)

                pvc_name = data["spec"]["volumeName"]
                code, data = self.lhvolumes.get(pvc_name)
                if not (200 == code and "detached" == data['status']['state']):
                    return False, (code, data)
            return True, (code, data)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_lhvolume_degraded(self, pv_name):
            code, data = api_client.lhvolumes.get(pv_name)
            if 200 == code and "degraded" == data['status']['robustness']:
                return True, (code, data)
            return False, (code, data)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_volumes_deleted(self, vol_names):
            for vol_name in vol_names:
                self.volumes.delete(name=vol_name)
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    code, data = self.volumes.get(name=vol_name)
                    if 404 == code:
                        break
                    sleep(sleep_timeout)
                if not (code == 404):
                    return False, (code, data)
            return True, (code, data)

    return VolumeChecker()
