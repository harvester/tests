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


@pytest.mark.skip()
@pytest.mark.terraform_provider_p1
@pytest.mark.p1
# This test covers terraform-5-Harvester image as a pre-req it covers
# terraform-1-install, terraform-2-kube config, terraform-3-define kube config
@pytest.mark.terraform
def test_create_images_using_terraform(admin_session, image_using_terraform):
    """
    Test creates Harvester Image

    Covers:
        terraform-provider-05-Harvester image as a pre-req it covers
        terraform-provider-01-install, terraform-provider-02-kube config,
        terraform-provider-03-define
        kube config
    """
    # NOTE: the image fixture will be creating the image and check the result
    pass
