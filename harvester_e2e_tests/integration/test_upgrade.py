import pytest


@pytest.fixture(scope="module")
def cluster_state(self):
    class ClusterState:
        pass

    return ClusterState()


@pytest.fixture(scope="module")
def cluster_prereq(self, api_client, cluster_state):
    # create cluster network
    # create a routable vlan
    cluster_state.clusternetwork = "cluster network name"
    cluster_state.vm_network = ("name", "vlanid", "cluster network name")
    cluster_state.vlan = "routable vlan id"


@pytest.fixture(scope="module")
def vm_prereq(self, api_client, cluster_state):
    cluster_state.old_target = "existing backup target" or ""
    # setup backup target
    # create new storage class, make it default
    # create 3 VMs:
    # - having the new storage class
    # - the VM that have some data written, take backup
    # - the VM restored from the backup
    # check VMs should able to reach each others (in same networks)

    cluster_state.storage_class = "Created storage class name"
    cluster_state.backup_name = "backup name from the VM"
    cluster_state.backup_target = "backup_target"
    cluster_state.vms = {
        "backed up": "backuped VM",
        "restored": "restored VM",
        "storage class": "VM having different storageclass"
    }


@pytest.mark.upgrade
@pytest.mark.any_nodes
@pytest.mark.negative
class TestInvalidUpgrade:
    def test_invalid_manifest(self):
        """
        Criteria: https://github.com/harvester/tests/issues/518

        Steps:
        1. Create an invalid manifest.
        2. Try to upgrade with the invalid manifest.
        3. Upgrade should not start and fail.
        """

    def test_degraded_volume(self):
        """
        Criteria: create upgrade should fails if there are any degraded volumes

        Steps:
        1. Create a VM using a volume with 3 replicas.
        2. Delete one replica of the volume. Let the volume stay in
           degraded state.
        3. Immediately upgrade Harvester.
        4. Upgrade should fail.
        """


@pytest.mark.upgrade
@pytest.mark.single_node
class TestSingleNodeUpgrade:
    @pytest.mark.dependency(name="single_node_upgrade")
    def test_perform_upgrade(self):
        pass


@pytest.mark.upgrade
@pytest.mark.three_nodes
class TestThreeNodesUpgrade:
    @pytest.mark.dependency(name="three_nodes_upgrade")
    def test_perform_upgrade(self, cluster_prereq, vm_prereq):
        """
        - perform upgrade
        - check all nodes upgraded
        """

    @pytest.mark.dependency(depends=["three_nodes_upgrade"])
    def test_verify_logging(self):
        """ Verify logging pods and logs
        Criteria: https://github.com/harvester/tests/issues/535
        """

    @pytest.mark.dependency(depends=["three_nodes_upgrade"])
    def test_verify_network(self, api_client, cluster_state):
        """ Verify cluster and VLAN networks
        - cluster network `mgmt` should exists
        - Created VLAN should exists
        """

    @pytest.mark.dependency(depends=["three_nodes_upgrade"])
    def test_verify_vms(self, api_client, cluster_state):
        """ Verify VMs' state and data
        Criteria:
        - VMs should keep in running state
        - data in VMs should not lost
        """

    @pytest.mark.dependency(depends=["three_nodes_upgrade"])
    def test_verify_restore_vm(self, api_client, cluster_state):
        """ Verify VM restored from the backup
        Criteria:
        - VM should able to start
        - data in VM should not lost
        """

    @pytest.mark.dependency(depends=["three_nodes_upgrade"])
    def test_verify_storage_class(self, api_client, cluster_state):
        """ Verify StorageClasses and defaults
        - `harvester-longhorn` should be settle as default
        - `longhorn` should exists
        """
