"""Check CDI readiness and the guard against deprovisioning live volumes."""

from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from kubernetes.client.rest import ApiException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "libs"))
from storageclass.crd import CRD  # noqa: E402


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.storage = CRD()
        self.storage.core_api = Mock()
        self.storage.custom_api = Mock()
        self.storage.core_api.list_persistent_volume_claim_for_all_namespaces.return_value = (
            SimpleNamespace(items=[])
        )
        self.storage.core_api.list_persistent_volume.return_value = SimpleNamespace(items=[])

    @staticmethod
    def volume(storage_class):
        return SimpleNamespace(spec=SimpleNamespace(storage_class_name=storage_class))

    def test_empty_storage_can_be_removed(self):
        self.assertTrue(self.storage.is_unused("cdi-test"))

    def test_pending_claim_blocks_removal(self):
        self.storage.core_api.list_persistent_volume_claim_for_all_namespaces.return_value = (
            SimpleNamespace(items=[self.volume("cdi-test")])
        )
        self.assertFalse(self.storage.is_unused("cdi-test"))

    def test_remaining_pv_blocks_removal(self):
        self.storage.core_api.list_persistent_volume.return_value = SimpleNamespace(
            items=[self.volume("cdi-test")]
        )
        self.assertFalse(self.storage.is_unused("cdi-test"))

    def test_unrelated_volumes_do_not_block_removal(self):
        self.storage.core_api.list_persistent_volume_claim_for_all_namespaces.return_value = (
            SimpleNamespace(items=[self.volume("other")])
        )
        self.storage.core_api.list_persistent_volume.return_value = SimpleNamespace(
            items=[self.volume(None)]
        )
        self.assertTrue(self.storage.is_unused("cdi-test"))

    def test_api_errors_do_not_allow_removal(self):
        methods = ("list_persistent_volume_claim_for_all_namespaces", "list_persistent_volume")
        for method in methods:
            with self.subTest(method=method):
                api_call = getattr(self.storage.core_api, method)
                api_call.side_effect = ApiException(status=403)
                with self.assertRaises(ApiException):
                    self.storage.is_unused("cdi-test")
                api_call.side_effect = None

    def test_missing_profile_is_not_ready(self):
        self.storage.custom_api.get_cluster_custom_object.side_effect = ApiException(status=404)
        self.assertIsNone(self.storage.get_profile("cdi-test"))

    def test_profile_api_errors_are_preserved(self):
        self.storage.custom_api.get_cluster_custom_object.side_effect = ApiException(status=403)
        with self.assertRaises(ApiException):
            self.storage.get_profile("cdi-test")


if __name__ == "__main__":
    unittest.main()
