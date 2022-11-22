import pytest


@pytest.mark.upgrade
@pytest.mark.skip(reason='TODO')
def test_pre_upgrade():
    """
    This test is to run on a setup before upgrade.

    Steps:
    1. Create a VM with OpenSuse image and Write some data into it.
    1. Verify the image, volume and network.
    1. Take a backup for the above created VM.
    1. Restore the above backup into a new VM.
    1. Stop the VMs
    """
    pass


@pytest.mark.upgrade
@pytest.mark.skip(reason='TODO')
def test_post_upgrade():
    """
    This test is to run on a setup after the upgrade. This test is dependent on
    the test_pre_upgrade test and can't be run alone.

    Steps:
    1. Do a check for the settings, CRDs etc that the setup is upgraded.
    1. Verify the resources, 2 VMs, 2 Volumes, 1 image, 1 Backup, network exist.
    1. Start 2 VMs which are in stop state.
    1. Verify the data in the VMs.
    1. Restore backup created in the Pre-upgrade test in a new VM.
    1. Verify the restored VM, check the data
    """
    pass
