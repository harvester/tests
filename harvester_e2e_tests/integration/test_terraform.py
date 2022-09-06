import pytest


@pytest.mark.skip()
def test_create_keypairs_using_terraform(keypair_using_terraform):
    """
    Test creates Harvester ssh key
    Covers:
    terraform-provider-04-Harvester ssh key as a pre-req it covers
    terraform-provider-01-install, terraform-provider-02-kube config,
    terraform-provider-03-define kube config
    """
    # keypair creation validation is done in the fixture already
    pass
