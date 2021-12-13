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
import polling2
import pytest
import requests


pytest_plugins = [
    'harvester_e2e_tests.fixtures.vm',
]


def _set_cluster_registration_url(admin_session, harvester_api_endpoints,
                                  manifest_url):
    # lookup Harvester cluster-registration-url
    resp = admin_session.get(
        harvester_api_endpoints.get_cluster_registration_url)
    assert resp.status_code == 200, (
        'Failed to lookup Harvester cluster-registration-url: %s: %s' % (
            resp.status_code, resp.content))
    cluster_reg_url_json = resp.json()

    # set Harvester cluster-registration-url
    cluster_reg_url_json['value'] = manifest_url
    resp = admin_session.put(
        harvester_api_endpoints.update_cluster_registration_url,
        json=cluster_reg_url_json)
    assert resp.status_code == 200, (
        'Failed to update cluster-registration-url: %s:%s' % (
            resp.status_code, resp.content))


def _delete_cluster(request, rancher_admin_session, rancher_api_endpoints,
                    cluster_name, harvester_cluster_id=None):
    resp = rancher_admin_session.delete(
        rancher_api_endpoints.delete_provisioning_cluster % (cluster_name))
    assert resp.status_code == 200, (
        'Failed to delete cluster %s: %s' % (cluster_name, resp.content))

    if harvester_cluster_id:
        resp = rancher_admin_session.delete(
            rancher_api_endpoints.delete_service_account_for_cluster % (
                harvester_cluster_id, cluster_name))
        assert resp.status_code == 204, (
            'Failed to delete Harvester service account for cluster %s' % (
                cluster_name))
        # TODO(gyee): do we need to check to make sure the corresponding VM is
        # deleted from Harvester?

    def _check_cluster_deleted():
        resp = rancher_admin_session.get(
            rancher_api_endpoints.get_provisioning_cluster % (cluster_name))
        if resp.status_code == 404:
            return True

    success = polling2.poll(
        _check_cluster_deleted,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))

    assert success, 'Timed out while waiting for cluster to be deleted.'


def _wait_for_cluster_ready(request, rancher_admin_session,
                            rancher_api_endpoints, cluster_name):
    def _wait_for_cluster_ready_status():
        resp = rancher_admin_session.get(
            rancher_api_endpoints.get_provisioning_cluster % (cluster_name))
        if resp.status_code == 200:
            cluster_json = resp.json()
            if ('status' in cluster_json and
                    'ready' in cluster_json['status']):
                return cluster_json['status']['ready']

    ready = polling2.poll(
        _wait_for_cluster_ready_status,
        step=5,
        timeout=request.config.getoption('--rancher-cluster-wait-timeout'))
    assert ready, 'Timed out while waiting to import Harvester.'


def _import_harvester_cluster_into_rancher(request, admin_session,
                                           harvester_api_endpoints,
                                           rancher_admin_session,
                                           rancher_api_endpoints):
    # Import Harvester Cluster
    request_json = utils.get_json_object_from_template(
        'import_harvester_cluster',
        test_environment=request.config.getoption('--test-environment')
    )
    resp = rancher_admin_session.post(
        rancher_api_endpoints.import_harvester_cluster,
        json=request_json)
    assert resp.status_code == 201, (
        'Failed to start importing harvester cluster %s: %s' % (
            resp.status_code, resp.content))
    cluster_name = resp.json()['metadata']['name']

    # wait for the cluster creation to complete by obtaining the cluster ID
    def _wait_for_cluster_id():
        resp = rancher_admin_session.get(
            rancher_api_endpoints.get_provisioning_cluster % (cluster_name))
        if resp.status_code == 200:
            cluster_json = resp.json()
            if ('status' in cluster_json and
                    'clusterName' in cluster_json['status']):
                return cluster_json['status']['clusterName']

    cluster_id = polling2.poll(
        _wait_for_cluster_id,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert cluster_id, 'Failed to lookup cluster ID.'

    # now get the manifestUrl

    def _wait_for_manifest_url():
        params = {"clusterId": cluster_id}
        try:
            resp = rancher_admin_session.get(
                rancher_api_endpoints.get_clusterregistrationtokens,
                params=params)
            if resp.status_code == 200:
                cluster_json = resp.json()
                if ('data' in cluster_json and
                        len(cluster_json['data']) > 0):
                    return cluster_json['data'][0]['manifestUrl']
        except Exception as e:
            print(e)

    manifest_url = polling2.poll(
        _wait_for_manifest_url,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert manifest_url, 'Timed out while waiting for manifest URL.'

    # register Harvester cluster
    _set_cluster_registration_url(admin_session, harvester_api_endpoints,
                                  manifest_url)

    # wait for cluster to be ready
    _wait_for_cluster_ready(request, rancher_admin_session,
                            rancher_api_endpoints, cluster_name)

    return (cluster_id, cluster_name)


@pytest.fixture(scope='class')
def external_rancher_with_imported_harvester(request, admin_session,
                                             harvester_api_endpoints,
                                             rancher_admin_session,
                                             rancher_api_endpoints):
    (cluster_id, cluster_name) = _import_harvester_cluster_into_rancher(
        request, admin_session, harvester_api_endpoints, rancher_admin_session,
        rancher_api_endpoints)

    yield cluster_id

    if not request.config.getoption('--do-not-cleanup'):
        # de-register the Harvester cluster prior to exist
        _set_cluster_registration_url(
            admin_session, harvester_api_endpoints, '')
        # delete the imported Harvester cluster from Rancher
        _delete_cluster(request, rancher_admin_session, rancher_api_endpoints,
                        cluster_name)


@pytest.fixture(scope='class')
def cloud_credential(request, rancher_admin_session, rancher_api_endpoints,
                     external_rancher_with_imported_harvester):
    test_environment = request.config.getoption('--test-environment')
    cluster_id = external_rancher_with_imported_harvester
    # Generate Kube config
    params = {'action': 'generateKubeconfig'}
    resp = rancher_admin_session.post(
        rancher_api_endpoints.generate_kubeconfig % (cluster_id),
        params=params)
    assert resp.status_code == 200, (
        'Failed to generate kubeconfig %s: %s' % (
            resp.status_code, resp.content))
    kube_json = resp.json()
    kubeconfig = kube_json['config']

    # Create cloud credentials
    request_json = utils.get_json_object_from_template(
        'rancher_cluster_cloud_credentials',
        test_environment=test_environment,
        cluster_id=cluster_id
    )
    request_json['harvestercredentialConfig']['kubeconfigContent'] = kubeconfig
    resp = rancher_admin_session.post(
        rancher_api_endpoints.create_cloud_credentials,
        json=request_json)
    assert resp.status_code == 201, (
        'Failed to create cloud credentials %s: %s' % (
            resp.status_code, resp.content))
    cred_json = resp.json()
    cloud_credential_id = cred_json['id']

    yield cloud_credential_id

    if not request.config.getoption('--do-not-cleanup'):
        resp = rancher_admin_session.delete(
            rancher_api_endpoints.delete_cloud_credential % (
                cloud_credential_id))
        assert resp.status_code == 204, (
            'Failed to delete cloud credential %s: %s' % (
                cloud_credential_id, resp.content))


@pytest.fixture(scope='class')
def rke2_cluster(request, rancher_admin_session, rancher_api_endpoints, image,
                 network, cloud_credential,
                 external_rancher_with_imported_harvester):
    test_environment = request.config.getoption('--test-environment')
    cluster_id = external_rancher_with_imported_harvester
    cloud_credential_id = cloud_credential

    # Harvester Kubeconfig
    rke2_cluster_name = 'rke2-' + test_environment
    rke2_cluster_name += '-' + utils.random_name()
    hkube_data = {'clusterRoleName': 'harvesterhci.io:cloudprovider',
                  'namespace': 'default',
                  'serviceAccountName': rke2_cluster_name,
                  'responseType': 'json'}
    resp = rancher_admin_session.post(
        rancher_api_endpoints.rke2_kubeconfig % (cluster_id),
        json=hkube_data)
    assert resp.status_code == 200, (
        'Failed to create rke2 kubeconfig %s: %s' % (
            resp.status_code, resp.content))
    harvkubeconfig = resp.json()

    # RKE2 machine config
    image_name = "/".join([image['metadata']['namespace'],
                          image['metadata']['name']])
    network_name = "/".join([network['metadata']['namespace'],
                            network['metadata']['name']])
    request_json = utils.get_json_object_from_template(
        'rancher_rke2_cluster_config',
        image_name=image_name,
        rke2_cluster_name=rke2_cluster_name,
        network_name=network_name
    )
    resp = rancher_admin_session.post(
        rancher_api_endpoints.rke2_machine_config,
        json=request_json)
    assert resp.status_code == 201, (
        'Failed to config rke2 cluster machine %s: %s' % (
            resp.status_code, resp.content))
    config_json = resp.json()
    pool_name = config_json['metadata']['name']

    # Provision RKE2 cluster
    kubernetes_version = request.config.getoption('--kubernetes-version')
    request_json = utils.get_json_object_from_template(
        'rancher_provision_rke2_cluster',
        name=rke2_cluster_name,
        cloud_credential_id=cloud_credential_id,
        rke2_cluster_name=rke2_cluster_name,
        pool_name=pool_name,
        kubernetes_version=kubernetes_version
    )
    request_json['spec']['rkeConfig']['machineSelectorConfig'][0][
        'config']['cloud-provider-config'] = harvkubeconfig
    resp = rancher_admin_session.post(
        rancher_api_endpoints.provision_rke2_cluster,
        json=request_json)
    assert resp.status_code == 201, (
        'Failed to provision rke2 cluster %s: %s' % (
            resp.status_code, resp.content))

    # wait for provision to successfully complete
    # wait for cluster to be ready
    _wait_for_cluster_ready(request, rancher_admin_session,
                            rancher_api_endpoints, rke2_cluster_name)

    yield rke2_cluster_name

    if not request.config.getoption('--do-not-cleanup'):
        # delete the imported Harvester cluster from Rancher
        _delete_cluster(request, rancher_admin_session, rancher_api_endpoints,
                        rke2_cluster_name, cluster_id)


@pytest.mark.rancher_integration_with_external_rancher
class TestRancherIntegrationWithExternalRancher:

    def test_import_harvester_into_rancher(
            self, external_rancher_with_imported_harvester):
        # if the external_rancher_with_imported_harvester fixture is
        # successfully created this test is golden
        pass

    @pytest.mark.skip('Need to figure out how to cleanup since we are '
                      'sharing a Rancher instance')
    def test_add_prj_owner_user(self, rancher_admin_session,
                                rancher_api_endpoints,
                                external_rancher_with_imported_harvester):
        cluster_id = external_rancher_with_imported_harvester
        request_json = utils.get_json_object_from_template(
            'rancher_user',
            password="projectowner",
            username="project-owner"
        )
        resp = rancher_admin_session.post(
            rancher_api_endpoints.create_user,
            json=request_json)
        assert resp.status_code == 201, (
            'Failed to create user project-owner %s: %s' % (
                resp.status_code, resp.content))
        user_json = resp.json()
        user_id = user_json['id']

        role_data = {'type': 'globalRoleBinding', 'globalRoleId': 'user',
                     'userId': user_id, 'responseType': 'json'}
        resp = rancher_admin_session.post(
            rancher_api_endpoints.create_global_role_binding,
            json=role_data)
        assert resp.status_code == 201, (
            'Failed to create global role binding %s: %s' % (
                resp.status_code, resp.content))

        # Get project Id
        resp = rancher_admin_session.get(
            rancher_api_endpoints.get_project_id % (cluster_id))
        assert resp.status_code == 200, (
            'Failed to project info %s: %s' % (resp.status_code, resp.content))
        proj_json = resp.json()['data']
        for proj in proj_json:
            if proj['spec']['displayName'] == 'Default':
                proj_name = proj['metadata']['name']
                break

        # Search principal
        search_data = {'name': 'project-owner', 'principalType': None,
                       'responseType': 'json'}
        params = {'action': 'search'}
        resp = rancher_admin_session.post(
            rancher_api_endpoints.search_principals,
            params=params, json=search_data)
        assert resp.status_code == 200, (
            'Failed to get project-owner user %s: %s' % (
                resp.status_code, resp.content))
        principal_json = resp.json()
        user_principal_id = principal_json['data'][0]['id']

        project_id = cluster_id + ":" + proj_name
        # Set pod security template
        pod_data = {'podSecurityPolicyTemplateId': None,
                    'responseType': 'json'}
        params = {'action': 'setpodsecuritypolicytemplate'}
        resp = rancher_admin_session.post(
            rancher_api_endpoints.set_podsecuritypolicytemplate % (project_id),
            params=params, json=pod_data)
        assert resp.status_code == 200, (
            'Failed to set  %s: %s' % (
                resp.status_code, resp.content))

        # Create project role template bindings
        role_bind_data = {'type': 'projectRoleTemplateBinding',
                          'roleTemplateId': 'project-owner',
                          'userPrincipalId': user_principal_id,
                          'projectId': project_id, 'responseType': 'json'}
        resp = rancher_admin_session.post(
            rancher_api_endpoints.create_projectroletemplatebinding,
            json=role_bind_data)
        assert resp.status_code == 201, (
            'Failed to create project role binding %s: %s' % (
                resp.status_code, resp.content))

        # Login to rancher using project-owner
        login_data = {'username': 'project-owner', 'password': 'projectowner',
                      'responseType': 'json'}
        params = {'action': 'login'}
        s = requests.Session()
        s.verify = False
        resp = s.post(rancher_api_endpoints['local_auth'],
                      params=params, json=login_data)
        assert resp.status_code == 201, 'Failed to authenticate user: %s' % (
            resp.content)

        auth_token = 'Bearer ' + resp.json()['token']
        s.headers.update({'Authorization': auth_token})

#        resp = s.get(rancher_api_endpoints['get_virtualmachines'] % (
#                cluster_id))
#        assert resp.status_code == 200, (
#            'Failed to get virtaul machines  %s: %s' % (
#                resp.status_code, resp.content))

    def test_create_rke2_cluster(self, request, rke2_cluster):
        # NOTE(gyee): if rke2_cluster fixture is successfully created that
        # means we're golden
        pass
