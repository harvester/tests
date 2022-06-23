from harvester_e2e_tests import utils
import pytest


@pytest.fixture(scope='class')
def support_bundle(request, kubevirt_api_version, admin_session,
                   harvester_api_endpoints):
    request_json = utils.get_json_object_from_template(
        'support_bundle',
        name='testing-e2e-api-support-bundle',
        description='A testing based support bundle',
        issue_url=''
    )
    resp = admin_session.post(harvester_api_endpoints.create_support_bundle,
                              json=request_json)
    assert resp.status_code == 201, ('Unable to create a basic ' +
                                     'supportbundle: %s' % (resp.content))
    support_bundle_data = resp.json()
    yield support_bundle_data
