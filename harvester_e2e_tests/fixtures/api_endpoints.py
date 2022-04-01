# Copyright (c) 2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

from harvester_e2e_tests import utils
import pytest


pytest_plugins = [
   'harvester_e2e_tests.fixtures.api_version',
  ]


# NOTE: see Swagger API doc here
# https://docs.harvesterhci.io/latest/reference/api/
class HarvesterAPIEndpoints:
    def __init__(self, endpoint, harvester_api_version,
                 cdi_api_version, kubevirt_api_version):
        self.harvester_endpoint = endpoint
        self.__dict__.update(
            utils.get_json_object_from_template(
                'api_endpoints',
                harvester_endpoint=self.harvester_endpoint,
                harvester_api_version=harvester_api_version,
                cdi_api_version=cdi_api_version,
                kubevirt_api_version=kubevirt_api_version
            )
        )


@pytest.fixture(scope='session')
def harvester_api_endpoints(request, harvester_api_version,
                            cdi_api_version, kubevirt_api_version):
    harvester_endpoint = request.config.getoption('--endpoint')
    return HarvesterAPIEndpoints(harvester_endpoint, harvester_api_version,
                                 cdi_api_version, kubevirt_api_version)


class RancherAPIEndpoints:
    def __init__(self, rancher_endpoint):
        self.rancher_endpoint = rancher_endpoint
        self.__dict__.update(
            utils.get_json_object_from_template(
                'rancher_api_endpoints',
                rancher_endpoint=rancher_endpoint
            )
        )


@pytest.fixture(scope='session')
def rancher_api_endpoints(request):
    rancher_endpoint = request.config.getoption('--rancher-endpoint')
    return RancherAPIEndpoints(rancher_endpoint)
