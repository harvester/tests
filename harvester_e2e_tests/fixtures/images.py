from urllib.parse import urlparse, urljoin

import pytest
from .base import wait_until

pytest_plugins = ["harvester_e2e_tests.fixtures.api_client"]

DEFAULT_UBUNTU_IMAGE_URL = (
    "https://cloud-images.ubuntu.com"
    "/focal/current/focal-server-cloudimg-amd64.img"
)


@pytest.fixture(scope="session")
def image_opensuse(request, api_client):
    image_server = request.config.getoption("--image-cache-url")
    image_checksum = request.config.getoption("--opensuse-checksum", default=None)
    url = urlparse(
        request.config.getoption("--opensuse-image-url")
    )

    if image_server:
        *_, image_name = url.path.rsplit("/", 1)
        url = urlparse(urljoin(f"{image_server}/", image_name))

    return ImageInfo(url, image_checksum, name="opensuse", ssh_user="opensuse")


@pytest.fixture(scope="session")
def image_ubuntu(request):
    image_server = request.config.getoption("--image-cache-url")
    image_checksum = request.config.getoption("--ubuntu-checksum", default=None)
    url = urlparse(
        request.config.getoption("--ubuntu-image-url") or DEFAULT_UBUNTU_IMAGE_URL
    )

    if image_server:
        *_, image_name = url.path.rsplit("/", 1)
        url = urlparse(urljoin(f"{image_server}/", image_name))

    return ImageInfo(url, image_checksum, name="ubuntu", ssh_user="ubuntu")


@pytest.fixture(scope="session")
def image_k3s(request):
    external = "https://github.com/rancher/k3os/releases/download/v0.20.11-k3s2r1/"
    base_url = request.config.getoption("--image-cache-url") or external
    url = urlparse(urljoin(f"{base_url}/", "k3os-amd64.iso"))

    return ImageInfo(url, ssh_user="k3s")


class ImageInfo:
    def __init__(self, url_result, image_checksum=None, name="", ssh_user=None):
        self.url_result = url_result
        if name:
            self.name = name
        else:
            self.name = self.url.rsplit("/", 1)[-1]
        self.ssh_user = ssh_user
        self.image_checksum = image_checksum

    def __repr__(self):
        return f"{__class__.__name__}({self.url_result})"

    @property
    def is_file(self):
        return "file" == self.url_result.scheme

    @property
    def url(self):
        if self.is_file:
            return self.url_result.geturl().split("file://", 1)[-1]
        return self.url_result.geturl()


@pytest.fixture(scope="session")
def image_checker(api_client, wait_timeout, sleep_timeout):
    class ImageChecker:
        def __init__(self):
            self.images = api_client.images

        @wait_until(wait_timeout, sleep_timeout)
        def wait_downloaded(self, image_name):
            code, data = self.images.get(image_name)
            if data.get('status', {}).get('progress') == 100:
                return True, (code, data)
            return False, (code, data)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_deleted(self, image_name):
            code, data = self.images.get(image_name)
            if code == 404:
                return True, (code, data)
            return False, (code, data)

    return ImageChecker()
