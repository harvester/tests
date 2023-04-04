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


@pytest.mark.skip("get_vlan API removed")
@pytest.mark.terraform_provider_p1
@pytest.mark.p1
@pytest.mark.terraform
@pytest.mark.public_network
def test_create_network_using_terraform(request, admin_session,
                                        harvester_api_endpoints,
                                        network_using_terraform):
    """
    Test creates Terraform Harvester
    Covers:
        terraform-provider-06-Harvester network as a pre-req it covers
        terraform-provider-08-Harvester cluster network during enable vlan
        terraform-provider-01-install, terraform-provider-02-kube config,
        terraform-provider-03-define
        kube config
    """
    pass


@pytest.mark.terraform_provider_p1
@pytest.mark.p1
@pytest.mark.terraform
def test_create_volume_using_terraform(admin_session, volume_using_terraform):
    """
    Test creates Terraform Harvester
    Covers:
        terraform-provider-07-Harvester volume
        terraform-provider-10-All resource terraform plan,apply,
        terraform destroy
        terraform-provider-01-install, terraform-provider-02-kube config,
        terraform-provider-03-define
        kube config
    """
    # NOTE: the volume_using_terraform fixture will be creating the
    # volume and check the result
    pass


@pytest.mark.skip(reason='Timing Issue')
@pytest.mark.terraform
def test_create_vol_with_image_terraform(admin_session,
                                         volume_with_image_using_terraform):
    # NOTE: the volume_using_terraform fixture will be creating the
    # volume and check the result
    pass
