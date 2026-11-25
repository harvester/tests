"""Version lookup must work for CRD suites without a Harvester REST login."""

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

from kubernetes.client.rest import ApiException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "libs"))
from keywords.addon_keywords import addon_keywords  # noqa: E402
from utility import utility  # noqa: E402


class VersionTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict("os.environ", {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.rest = patch.object(utility, "get_harvester_api_client")
        self.rest_client = self.rest.start()
        self.addCleanup(self.rest.stop)
        self.crd = patch("crd.get_cluster_cr")
        self.get_setting = self.crd.start()
        self.addCleanup(self.crd.stop)
        self.get_setting.return_value = {"value": "release-v1.9.0-rc5-b117-head"}

    def test_crd_install_needs_no_rest_login(self):
        self.rest_client.side_effect = RuntimeError("REST client not initialized")
        keywords = addon_keywords()
        keywords.install_addon_yaml = Mock()

        keywords.install_experimental_addon("harvester-csi-driver-lvm")

        self.rest_client.assert_not_called()
        self.get_setting.assert_called_once_with(
            group="harvesterhci.io", version="v1beta1",
            plural="settings", name="server-version"
        )
        keywords.install_addon_yaml.assert_called_once_with(
            "https://raw.githubusercontent.com/harvester/harvester/v1.9/"
            "addons/standalone/harvester-csi-driver-lvm/addon.yaml"
        )

    def test_dev_build_uses_master_manifest(self):
        self.get_setting.return_value = {"value": "3099e1e5"}
        keywords = addon_keywords()
        keywords.install_addon_yaml = Mock()

        keywords.install_experimental_addon("harvester-csi-driver-lvm")

        keywords.install_addon_yaml.assert_called_once_with(
            "https://raw.githubusercontent.com/harvester/harvester/master/"
            "addons/standalone/harvester-csi-driver-lvm/addon.yaml"
        )

    def test_crd_api_errors_are_preserved(self):
        self.get_setting.side_effect = ApiException(status=403)
        with self.assertRaises(ApiException):
            utility.get_cluster_version_release()

    @patch.dict("os.environ", {"HARVESTER_OPERATION_STRATEGY": "rest"})
    def test_rest_strategy_keeps_rest_lookup(self):
        self.rest_client.return_value.get.return_value = (200, {"value": "v1.8.2"})

        self.assertEqual(utility.get_cluster_version_release(), (1, 8, 2))

        self.get_setting.assert_not_called()
        self.rest_client.return_value.get.assert_called_once_with(
            "apis/harvesterhci.io/v1beta1/settings/server-version"
        )


if __name__ == "__main__":
    unittest.main()
