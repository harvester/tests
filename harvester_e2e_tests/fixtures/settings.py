import json
from ipaddress import ip_address, ip_network

import pytest
from .base import wait_until


@pytest.fixture(scope="session")
def setting_checker(api_client, wait_timeout, sleep_timeout):
    class SettingChecker:
        def __init__(self):
            self.settings = api_client.settings
            self.nets_annotation = 'k8s.v1.cni.cncf.io/networks'
            self.net_status_annotation = 'k8s.v1.cni.cncf.io/network-status'

        def _storage_net_configured(self):
            code, data = self.settings.get('storage-network')

            cs = data.get('status', {}).get('conditions')
            if cs:
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
                    return False, (f"Pod {imgr['id']} is not Running", imgr)

            return True, (None, lh_instance_mgrs)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_storage_net_enabled_on_longhorn(self, snet_cidr):
            imgrs_running, (code, data) = self._lh_instance_mgrs_running()
            if not imgrs_running:
                return False, (code, data)

            for imgr in data:
                annotations = imgr['metadata']['annotations']

                for na in [self.nets_annotation, self.net_status_annotation]:
                    if na not in annotations:
                        return False, (f"Pod has no annotation {na}", imgr)

                # Check k8s.v1.cni.cncf.io/networks
                try:
                    nets = json.loads(annotations[self.nets_annotation])
                    snet = next(n for n in nets if 'lhnet1' == n.get('interface'))
                except StopIteration:
                    msg = f"Annotation {self.nets_annotation} has no interface 'lhnet1'"
                    return False, (msg, imgr)

                # Check k8s.v1.cni.cncf.io/network-status
                try:
                    net_statuses = json.loads(annotations[self.net_status_annotation])
                    snet_status = next(s for s in net_statuses if 'lhnet1' == s.get('interface'))
                except StopIteration:
                    msg = f"Annotation {self.net_status_annotation} has no interface 'lhnet1'"
                    return False, (msg, imgr)

                snet_ips = snet_status.get('ips', ['::1'])
                if not all(ip_address(sip) in ip_network(snet_cidr) for sip in snet_ips):
                    return False, (f"Dedicated IPs {snet_ips} does NOT fits {snet_cidr}", imgr)

                # Check network name identical in both annotations
                if f"{snet.get('namespace')}/{snet.get('name')}" != snet_status.get('name'):
                    msg = "Network name is not identical between annotations {} and {}".format(
                        self.nets_annotation, self.net_status_annotation)
                    return False, (msg, imgr)

            return True, (None, None)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_storage_net_disabled_on_longhorn(self):
            imgrs_running, (code, data) = self._lh_instance_mgrs_running()
            if not imgrs_running:
                return False, (code, data)

            for imgr in data:
                if self.nets_annotation in imgr['metadata']['annotations']:
                    return False, (f"Pod should not has annotation {self.nets_annotation}", imgr)

            return True, (None, None)

    return SettingChecker()
