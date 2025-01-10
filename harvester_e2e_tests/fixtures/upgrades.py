import pytest
from .base import wait_until

pytest_plugins = ["harvester_e2e_tests.fixtures.api_client"]


@pytest.fixture(scope="session")
def upgrade_checker(api_client, wait_timeout, sleep_timeout):
    class UpgradeChecker:
        def __init__(self):
            self.versions = api_client.versions
            self.upgrades = api_client.upgrades

        @wait_until(wait_timeout, sleep_timeout)
        def wait_upgrade_version_created(self, version):
            code, data = self.versions.get(version)
            if code == 200:
                return True, (code, data)
            return False, (code, data)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_upgrade_fail_by_invalid_iso_url(self, upgrade_name):
            code, data = self.upgrades.get(upgrade_name)
            conds = dict((c['type'], c) for c in data.get('status', {}).get('conditions', []))
            verified = [
                "False" == conds.get('Completed', {}).get('status'),
                "False" == conds.get('ImageReady', {}).get('status'),
                "no such host" in conds.get('ImageReady', {}).get('message', "")
            ]
            if all(verified):
                return True, (code, data)
            return False, (code, data)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_upgrade_fail_by_invalid_checksum(self, upgrade_name):
            code, data = self.upgrades.get(upgrade_name)
            conds = dict((c['type'], c) for c in data.get('status', {}).get('conditions', []))
            verified = [
                "False" == conds.get('Completed', {}).get('status'),
                "False" == conds.get('ImageReady', {}).get('status'),
                "n't match the file actual check" in conds.get('ImageReady', {}).get('message', "")
            ]
            if all(verified):
                return True, (code, data)
            return False, (code, data)

    return UpgradeChecker()
