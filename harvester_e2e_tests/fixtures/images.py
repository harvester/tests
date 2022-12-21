from urllib.parse import urlparse, urljoin

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]


@pytest.fixture(scope="session")
def opensuse_image(request, api_client):
    image_server = request.config.getoption('--image-cache-url')
    url = urlparse(request.config.getoption('--opensuse-image-url'))

    if image_server:
        *_, image_name = url.path.rsplit('/', 1)
        url = urlparse(urljoin(image_server, image_name))

    return ImageInfo(url)


class ImageInfo:
    def __init__(self, url_result):
        self.url_result = url_result
        self.name = self.url.rsplit('/', 1)[-1]

    def __repr__(self):
        return f"{__class__.__name__}({self.url_result})"

    @property
    def is_file(self):
        return 'file' == self.url_result.scheme

    @property
    def url(self):
        if self.is_file:
            return self.url_result.geturl().split('file://', 1)[-1]
        return self.url_result.geturl()
