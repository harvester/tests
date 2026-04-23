"""
Storage Network Keywords - creates StorageNetwork() instance and delegates
Layer 3: Keyword wrappers for Robot Framework
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))  # noqa E402
from utility.utility import logging  # noqa E402
from storage_network import StorageNetwork  # noqa E402
from constant import DEFAULT_TIMEOUT  # noqa E402


class storage_network_keywords:
    """Storage Network keyword wrapper - creates StorageNetwork component and delegates"""

    def __init__(self):
        """Initialize storage network keywords with lazy loading"""
        self._storage_network = None

    @property
    def storage_network(self):
        """Lazy initialize storage network to allow API client setup first"""
        if self._storage_network is None:
            self._storage_network = StorageNetwork()
        return self._storage_network

    def enable_storage_network(self, vlan_id, cluster_network, ip_range,
                               share_rwx=False):
        """
        Enable the storage-network Harvester setting.

        Args:
            vlan_id: VLAN ID for the storage network
            cluster_network: Cluster network name
            ip_range: CIDR IP range for storage network
            share_rwx: If True, share storage network for RWX volumes
        """
        logging(f"Enabling storage network: vlan={vlan_id}, "
                f"cluster_network={cluster_network}, ip_range={ip_range}, "
                f"share_rwx={share_rwx}")
        # Robot Framework ${TRUE} passes as Python bool, but handle strings too
        rwx = share_rwx if isinstance(share_rwx, bool) else str(share_rwx).lower() == 'true'
        self.storage_network.enable_storage_network(
            vlan_id, cluster_network, ip_range,
            share_rwx=rwx
        )

    def disable_storage_network(self):
        """Disable the storage-network Harvester setting."""
        logging("Disabling storage network")
        self.storage_network.disable_storage_network()

    def get_storage_network_status(self):
        """
        Get the current storage-network setting status.

        Returns:
            dict: The storage-network setting data
        """
        logging("Getting storage-network status")
        return self.storage_network.get_storage_network_status()

    def wait_for_storage_network_ready(self, timeout=DEFAULT_TIMEOUT):
        """
        Wait for storage-network setting to be applied and completed.

        Args:
            timeout: Timeout in seconds

        Returns:
            dict: Storage network data when ready
        """
        logging("Waiting for storage-network to be ready")
        return self.storage_network.wait_for_storage_network_ready(
            int(timeout)
        )

    def get_vlan_network_cidr(self, vlan_id, cluster_network):
        """
        Get the CIDR for a VLAN network by creating a temporary network.

        Args:
            vlan_id: VLAN ID
            cluster_network: Cluster network name

        Returns:
            str: CIDR string
        """
        logging(f"Getting VLAN network CIDR for vlan={vlan_id}")
        return self.storage_network.get_vlan_network_cidr(
            vlan_id, cluster_network
        )

    def enable_longhorn_rwx_storage_network(self):
        """Set the Longhorn endpoint-network-for-rwx-volume setting."""
        logging("Setting Longhorn RWX endpoint network")
        self.storage_network.enable_longhorn_rwx_storage_network()

    def disable_longhorn_rwx_storage_network(self):
        """Clear the Longhorn endpoint-network-for-rwx-volume setting."""
        logging("Clearing Longhorn RWX endpoint network")
        self.storage_network.disable_longhorn_rwx_storage_network()
