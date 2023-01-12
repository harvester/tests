import pytest
from time import sleep
from datetime import datetime, timedelta

pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.api_client',
    'harvester_e2e_tests.fixtures.volume',
    'harvester_e2e_tests.fixtures.session',
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.images',
]


@pytest.mark.images_p1
@pytest.mark.dependency(name="create_image_url")
def test_create_with_url(api_client, opensuse_image, unique_name, wait_timeout):
    """
    Test if you can create an image from a URL.

    Prerequisite:
    Setting opensuse-image-url set to a valid URL for
    an opensuse image.

    1. Create an image from URL.
    2. Check for 201 response.
    3. loop until the image has conditions.
    4. Check if the image is intialzied and the status is true
    5. Remove image
    """
    code, data = api_client.images.create_by_url(unique_name, opensuse_image.url)
    assert 201 == code, (
                f"Failed to create image {unique_name} from URL got\n"
                f"Creation got {code} with {data}"
    )
    endtime = datetime.now() + timedelta(wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(unique_name)
        image_conds = data.get('status', {}).get('conditions', [])
        if len(image_conds) > 0:
            break
        sleep(3)

    assert "Initialized" == image_conds[-1].get("type")
    assert "True" == image_conds[-1].get("status")
    api_client.images.delete(unique_name)
