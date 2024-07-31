import json
from ipaddress import ip_address, ip_network

import pytest
from .base import wait_until


@pytest.fixture(scope="session")
def setting_checker(api_client, wait_timeout, sleep_timeout):
    class SettingChecker:
        def __init__(self):
            self.settings = api_client.settings
            self.network_annotation = 'k8s.v1.cni.cncf.io/network-status'

        def _storage_net_configured(self):
            code, data = self.settings.get('storage-network')
            if (cs := data.get('status', {}).get('conditions')):
                if 'True' == cs[-1].get('status') and 'Completed' == cs[-1].get('reason'):
                    return True, (code, data)
            return False, (code, data)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_storage_net_enabled_on_harvester(self):
            snet_configured, (code, data) = self._storage_net_configured()
            if snet_configured and data.get('value'):
                return True, (code, data)
            return False, (code, data)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_storage_net_disabled_on_harvester(self):
            snet_configured, (code, data) = self._storage_net_configured()
            if snet_configured and not data.get('value'):
                return True, (code, data)
            return False, (code, data)

        def _lh_instance_mgrs_running(self):
            code, data = api_client.get_pods(namespace='longhorn-system')
            if not (code == 200):
                return False, (code, data)

            lh_instance_mgrs = [pod for pod in data['data'] if 'instance-manager' in pod['id']]
            if not lh_instance_mgrs:
                return False, ("No instance-manager pods", data)

            for imgr in lh_instance_mgrs:
                if 'Running' != imgr['status']['phase']:
                    return False, (f"Pod {imgr['id']} is NOT Running", imgr)

                if not (self.network_annotation in imgr['metadata']['annotations']):
                    return False, (f"No annotation '{self.network_annotation}' on pod", imgr)

                networks = json.loads(imgr['metadata']['annotations'][self.network_annotation])
                if not networks:
                    return False, (f"Pod annotation '{self.network_annotation}' is empty", imgr)

            return True, (None, lh_instance_mgrs)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_storage_net_enabled_on_longhorn(self, snet_cidr):
            imgrs_running, (code, data) = self._lh_instance_mgrs_running()
            if not imgrs_running:
                return False, (code, data)

            for imgr in data:
                networks = json.loads(imgr['metadata']['annotations'][self.network_annotation])
                try:
                    snet_network = next(n for n in networks if 'lhnet1' == n.get('interface'))
                except StopIteration:
                    return False, ("No dedicated interface interface 'lhnet1'", imgr)

                snet_ips = snet_network.get('ips', ['::1'])
                if not all(ip_address(sip) in ip_network(snet_cidr) for sip in snet_ips):
                    return False, (f"Dedicated IPs {snet_ips} does NOT fits {snet_cidr}", imgr)

            return True, (None, None)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_storage_net_disabled_on_longhorn(self):
            imgrs_running, (code, data) = self._lh_instance_mgrs_running()
            if not imgrs_running:
                return False, (code, data)

            for imgr in data:
                networks = json.loads(imgr['metadata']['annotations'][self.network_annotation])
                try:
                    next(n for n in networks if 'lhnet1' == n.get('interface'))
                    return False, ("No dedicated interface 'lhnet1'", imgr)
                except StopIteration:
                    continue

            return True, (None, None)

    return SettingChecker()
