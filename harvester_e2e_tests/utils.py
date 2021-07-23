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

import jinja2
import json
import math
import os
import polling2
import random
import string
import subprocess
import time
import uuid
import yaml


def random_name():
    """Generate a random alphanumeric name using uuid.uuid4()"""
    return uuid.uuid4().hex


def random_alphanumeric(length=5, upper_case=False):
    """Generate a random alphanumeric string of given length

    :param length: the size of the string
    :param upper_case: whether to return the upper case string
    """
    if upper_case:
        return ''.join(random.choice(
            string.ascii_uppercase + string.digits) for _ in range(length))
    else:
        return ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(length))


def get_json_object_from_template(template_name, **template_args):
    """Load template from template file

    :param template_name: the name of the template. It is the filename of
                          template without the file extension. For example, if
                          you want to load './templates/foo.json.j2', then the
                          template_name should be 'foo'.
    :param template_args: dictionary of template argument values for the given
                          Jinja2 template
    """
    # get the current path relative to the ./templates/ directory
    my_path = os.path.dirname(os.path.realpath(__file__))
    # NOTE: the templates directory must be at the same level as
    # utilities.py, and all the templates must have the '.yaml.j2' extension
    templates_path = os.path.join(my_path, 'templates')
    template_file = f'{templates_path}/{template_name}.json.j2'
    # now load the template
    with open(template_file) as tempfile:
        template = jinja2.Template(tempfile.read())
    template.globals['random_name'] = random_name
    template.globals['random_alphanumeric'] = random_alphanumeric
    # now render the template
    rendered = template.render(template_args)
    return json.loads(rendered)


def poll_for_resource_ready(request, admin_session, endpoint,
                            expected_code=200):
    ready = polling2.poll(
        lambda: admin_session.get(endpoint).status_code == expected_code,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert ready, 'Timed out while waiting for %s to yield %s' % (
        endpoint, expected_code)


def get_latest_resource_version(request, admin_session, lookup_endpoint):
    poll_for_resource_ready(request, admin_session, lookup_endpoint)
    resp = admin_session.get(lookup_endpoint)
    assert resp.status_code == 200, 'Failed to lookup resource: %s' % (
        resp.content)
    return resp.json()['metadata']['resourceVersion']


def poll_for_update_resource(request, admin_session, update_endpoint,
                             request_json, lookup_endpoint, use_yaml=None):

    resp = None

    def _update_resource():
        # we want the update response to return back to the caller
        nonlocal resp

        # first we need to get the latest resourceVersion and fill that in
        # the request_json as it is a required field and must be the latest.
        request_json['metadata']['resourceVersion'] = (
            get_latest_resource_version(
                request, admin_session, lookup_endpoint))
        if use_yaml:
            resp = admin_session.put(update_endpoint,
                                     data=yaml.dump(
                                         request_json, sort_keys=False),
                                     headers={
                                         'Content-Type': 'application/yaml'})
        else:
            resp = admin_session.put(update_endpoint, json=request_json)
        if resp.status_code == 409:
            return False
        else:
            assert resp.status_code == 200, 'Failed to update resource: %s' % (
                resp.content)
            return True

    # NOTE(gyee): we need to do retries because kubenetes cluster does not
    # guarantee freshness when updating resources because of the way it handles
    # queuing. See
    # https://github.com/kubernetes/kubernetes/issues/84430
    # Therefore, we must do fetch-retry when updating resources.
    # Apparently this is way of life in Kubernetes world.
    updated = polling2.poll(
        _update_resource,
        step=3,
        timeout=120)
    assert updated, 'Timed out while waiting to update resource: %s' % (
        update_endpoint)
    return resp


def lookup_vm_instance(admin_session, harvester_api_endpoints, vm_json):
    # NOTE(gyee): seem like the corresponding VM instance has the same name as
    # the VM. If this assumption is not true, we need to fix this code.
    resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
        vm_json['metadata']['name']))
    assert resp.status_code == 200, 'Failed to lookup VM instance %s: %s' % (
        vm_json['metadata']['name'], resp.content)
    return resp.json()


def lookup_hosts_with_most_available_cpu(admin_session,
                                         harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    nodes_json = resp.json()['data']
    most_available_cpu_nodes = None
    most_available_cpu = 0
    for node in nodes_json:
        # look up CPU usage for the given node
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node['metadata']['name']))
        assert resp.status_code == 200, (
            'Failed to lookup metrices for node %s: %s' % (
                node['metadata']['name'], resp.content))
        metrics_json = resp.json()
        # NOTE: Kubernets CPU metrics are expressed in nanocores, or
        # 1 billionth of a CPU. We need to convert it to a whole CPU core.
        cpu_usage = math.ceil(
            int(metrics_json['usage']['cpu'][:-1]) / 1000000000)
        available_cpu = int(node['status']['allocatable']['cpu']) - cpu_usage
        if available_cpu > most_available_cpu:
            most_available_cpu = available_cpu
            most_available_cpu_nodes = [node['metadata']['name']]
        elif available_cpu == most_available_cpu:
            most_available_cpu_nodes.append(node['metadata']['name'])
    return (most_available_cpu_nodes, most_available_cpu)


def lookup_hosts_with_most_available_memory(admin_session,
                                            harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    nodes_json = resp.json()['data']
    most_available_memory_nodes = None
    most_available_memory = 0
    for node in nodes_json:
        # look up CPU usage for the given node
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node['metadata']['name']))
        assert resp.status_code == 200, (
            'Failed to lookup metrices for node %s: %s' % (
                node['metadata']['name'], resp.content))
        metrics_json = resp.json()
        # NOTE: Kubernets memory metrics are expressed Kibibyte so convert it
        # back to Gigabytes
        memory_usage = math.ceil(
            int(metrics_json['usage']['memory'][:-2]) * 1.024e-06)
        # NOTE: we want the floor here so we don't over commit
        allocatable_memory = int(node['status']['allocatable']['memory'][:-2])
        allocatable_memory = math.floor(
            allocatable_memory * 1.024e-06)
        available_memory = allocatable_memory - memory_usage
        if available_memory > most_available_memory:
            most_available_memory = available_memory
            most_available_memory_nodes = [node['metadata']['name']]
        elif available_memory == most_available_memory:
            most_available_memory_nodes.append(node['metadata']['name'])
    return (most_available_memory_nodes, most_available_memory)


def lookup_hosts_with_cpu_and_memory(admin_session, harvester_api_endpoints,
                                     cpu, memory):
    """Lookup nodes that satisfies the given CPU and memory requirements"""
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    nodes_json = resp.json()['data']
    nodes = []
    for node in nodes_json:
        # look up CPU usage for the given node
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node['metadata']['name']))
        assert resp.status_code == 200, (
            'Failed to lookup metrices for node %s: %s' % (
                node['metadata']['name'], resp.content))
        metrics_json = resp.json()
        # NOTE: Kubernets CPU metrics are expressed in nanocores, or
        # 1 billionth of a CPU. We need to convert it to a whole CPU core.
        cpu_usage = math.ceil(
            int(metrics_json['usage']['cpu'][:-1]) / 1000000000)
        available_cpu = int(node['status']['allocatable']['cpu']) - cpu_usage
        # NOTE: Kubernets memory metrics are expressed Kibibyte so convert it
        # back to Gigabytes
        memory_usage = math.ceil(
            int(metrics_json['usage']['memory'][:-2]) * 1.024e-06)
        # NOTE: we want the floor here so we don't over commit
        allocatable_memory = int(node['status']['allocatable']['memory'][:-2])
        allocatable_memory = math.floor(
            allocatable_memory * 1.024e-06)
        available_memory = allocatable_memory - memory_usage
        if available_cpu >= cpu and available_memory >= memory:
            nodes.append(node['metadata']['name'])
    return nodes


def restart_vm(admin_session, harvester_api_endpoints, previous_uid, vm_name,
               wait_timeout):
    resp = admin_session.post(harvester_api_endpoints.restart_vm % (
        vm_name))
    assert resp.status_code == 204, 'Failed to restart VM instance %s: %s' % (
        vm_name, resp.content)
    assert_vm_restarted(admin_session, harvester_api_endpoints, previous_uid,
                        vm_name, wait_timeout)


def assert_vm_restarted(admin_session, harvester_api_endpoints,
                        previous_uid, vm_name, wait_timeout):
    # give it some time for the VM instance to restart
    time.sleep(120)

    def _check_vm_instance_restarted():
        resp = admin_session.get(
            harvester_api_endpoints.get_vm_instance % (vm_name))
        if resp.status_code == 200:
            resp_json = resp.json()
            if ('status' in resp_json and
                    'phase' in resp_json['status'] and
                    resp_json['status']['phase'] == 'Running' and
                    resp_json['metadata']['uid'] != previous_uid):
                return True
        return False

    success = polling2.poll(
        _check_vm_instance_restarted,
        step=5,
        timeout=wait_timeout)
    assert success, 'Failed to restart VM %s' % (vm_name)


def delete_image(request, admin_session, harvester_api_endpoints, image_json):
    resp = admin_session.delete(harvester_api_endpoints.delete_image % (
        image_json['metadata']['name']))
    assert resp.status_code in [200, 201], 'Unable to delete image %s: %s' % (
        image_json['metadata']['name'], resp.content)

    def _wait_for_image_to_be_deleted():
        resp = admin_session.get(harvester_api_endpoints.get_image % (
            image_json['metadata']['name']))
        if resp.status_code == 404:
            return True
        return False

    success = polling2.poll(
        _wait_for_image_to_be_deleted,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for image to be deleted'


def create_image(request, admin_session, harvester_api_endpoints, url,
                 name=None, description=''):
    request_json = get_json_object_from_template(
        'basic_image',
        name=name,
        description=description,
        url=url
    )
    resp = admin_session.post(harvester_api_endpoints.create_image,
                              json=request_json)
    assert resp.status_code in [200, 201], 'Failed to create image %s: %s' % (
        name, resp.content)
    image_json = resp.json()

    # wait for the image to get ready
    time.sleep(30)

    def _wait_for_image_become_active():
        # we want the update response to return back to the caller
        nonlocal image_json

        resp = admin_session.get(harvester_api_endpoints.get_image % (
            image_json['metadata']['name']))
        assert resp.status_code == 200, 'Failed to get image %s: %s' % (
            image_json['metadata']['name'], resp.content)
        image_json = resp.json()
        if ('status' in image_json and
                'storageClassName' in image_json['status']):
            return True
        return False

    success = polling2.poll(
        _wait_for_image_become_active,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for image to be active.'

    return image_json


def create_vm(request, admin_session, image, harvester_api_endpoints,
              template='basic_vm', keypair=None, volume=None, network=None,
              cpu=1, disk_size_gb=10, memory_gb=1, network_data=None,
              user_data=None, running=True):
    volume_name = None
    ssh_public_key = None
    network_name = None
    if network:
        network_name = network['metadata']['name']
    if volume:
        volume_name = volume['metadata']['name']
    if keypair:
        ssh_public_key = keypair['spec']['publicKey']
    request_json = get_json_object_from_template(
        template,
        image_namespace=image['metadata']['namespace'],
        image_name=image['metadata']['name'],
        image_storage_class=image['status']['storageClassName'],
        volume_name=volume_name,
        network_name=network_name,
        disk_size_gb=disk_size_gb,
        cpu=cpu,
        memory_gb=memory_gb,
        ssh_public_key=ssh_public_key,
        network_data=network_data,
        user_data=user_data
    )
    request_json['spec']['running'] = running
    resp = admin_session.post(harvester_api_endpoints.create_vm,
                              json=request_json)
    assert resp.status_code == 201, 'Failed to create VM'
    vm_resp_json = resp.json()
    if running:
        # wait for VM to be ready
        time.sleep(180)

    def _check_vm_ready():
        resp = admin_session.get(harvester_api_endpoints.get_vm % (
            vm_resp_json['metadata']['name']))
        if resp.status_code == 200:
            resp_json = resp.json()
            if running:
                if ('status' in resp_json and
                        'ready' in resp_json['status'] and
                        resp_json['status']['ready']):
                    return True
            else:
                if ('status' in resp_json and
                        'ready' not in resp_json['status']):
                    return True
        return False

    success = polling2.poll(
        _check_vm_ready,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for VM to be ready.'
    return vm_resp_json


def delete_vm(request, admin_session, harvester_api_endpoints, vm_json,
              remove_all_disks=True):
    params = {}
    if remove_all_disks:
        devices = vm_json['spec']['template']['spec']['domain']['devices']
        disk_names = [disk['name'] for disk in devices['disks']]
        params = {'removedDisks': ','.join(disk_names)}
    resp = admin_session.delete(harvester_api_endpoints.delete_vm % (
        vm_json['metadata']['name']), params=params)
    assert resp.status_code in [200, 201], 'Failed to delete VM %s: %s' % (
        vm_json['metadata']['name'], resp.content)

    def _check_vm_deleted():
        resp = admin_session.get(harvester_api_endpoints.get_vm % (
            vm_json['metadata']['name']))
        if resp.status_code == 404:
            return True
        return False

    success = polling2.poll(
        _check_vm_deleted,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for VM to be terminated.'


def delete_volume(request, admin_session, harvester_api_endpoints,
                  volume_json):
    resp = admin_session.delete(harvester_api_endpoints.delete_volume % (
        volume_json['metadata']['name']))
    assert resp.status_code in [200, 201], (
        'Failed to delete volume %s: %s' % (
            volume_json['metadata']['name'], resp.content))

    def _check_volume_deleted():
        resp = admin_session.get(harvester_api_endpoints.delete_volume % (
            volume_json['metadata']['name']))
        if resp.status_code == 404:
            return True
        return False

    success = polling2.poll(
        _check_volume_deleted,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for volume to be terminated.'


def delete_host(request, admin_session, harvester_api_endpoints, host_json):
    resp = admin_session.delete(harvester_api_endpoints.delete_node % (
        host_json['id']))
    assert resp.status_code in [200, 201], 'Unable to delete host %s: %s' % (
        host_json['id'], resp.content)
    # wait for host to be deleted
    time.sleep(180)

    def _wait_for_host_to_be_deleted():
        resp = admin_session.get(harvester_api_endpoints.get_node % (
            host_json['id']))
        if resp.status_code == 404:
            return True
        return False

    success = polling2.poll(
        _wait_for_host_to_be_deleted,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for host to be deleted'


def _get_node_script_path(request, script_name):
    scripts_dir = request.config.getoption('--node-scripts-location')
    assert scripts_dir, ('Node scripts location not provided. Please use '
                         'the --node-scripts-location parameter to specify '
                         'the location of the node scripts.')
    assert os.path.isdir(scripts_dir), 'Invalid node scripts location: %s' % (
        scripts_dir)
    script = os.path.join(scripts_dir, script_name)
    assert os.path.isfile(script), 'Node script %s not found' % (script)
    assert os.access(script, os.X_OK), 'Node script %s is not executable' % (
        script)
    return script


def power_off_node(request, admin_session, harvester_api_endpoints, node_name):
    power_off_script = _get_node_script_path(request, 'power_off.sh')
    result = subprocess.run([power_off_script, node_name], capture_output=True)
    assert result.returncode == 0, (
        'Failed to power-off node %s: rc: %s, stdout: %s, stderr: %s' % (
            node_name, result.returncode, result.stderr, result.stdout))

    # wait for the node to disappear
    time.sleep(120)

    def _wait_for_node_to_disappear():
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node_name))
        metrics_json = resp.json()
        if 'status' in metrics_json and metrics_json['status'] == 404:
            return True
        return False

    success = polling2.poll(
        _wait_for_node_to_disappear,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for node to shutdown'


def power_on_node(request, admin_session, harvester_api_endpoints, node_name):
    power_on_script = _get_node_script_path(request, 'power_on.sh')
    result = subprocess.run([power_on_script, node_name], capture_output=True)
    assert result.returncode == 0, (
        'Failed to power-on node %s: rc: %s, stdout: %s, stderr: %s' % (
            node_name, result.returncode, result.stderr, result.stdout))

    # wait for the node to power-on
    time.sleep(180)

    def _wait_for_node_to_appear():
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node_name))
        metrics_json = resp.json()
        if ('metadata' in metrics_json and
                'state' in metrics_json['metadata'] and
                metrics_json['metadata']['state']['error'] is False):
            return True
        return False

    success = polling2.poll(
        _wait_for_node_to_appear,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for node to power-on'


def lookup_host_not_harvester_endpoint(request, admin_session,
                                       harvester_api_endpoints):
    cur_endpoint = (request.config.getoption('--endpoint').split(":")[1])[2:]
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    nodes_json = resp.json()['data']
    for node in nodes_json:
        # look up CPU usage for the given node
        if node['metadata']['annotations'].get(
                'etcd.k3s.cattle.io/node-address') != cur_endpoint:
            node_data = node
    return node_data


def reboot_node(request, admin_session, harvester_api_endpoints, node_name):
    reboot_script = _get_node_script_path(request, 'reboot.sh')
    result = subprocess.run([reboot_script, node_name], capture_output=True)
    assert result.returncode == 0, (
        'Failed to reboot node %s: rc: %s, stdout: %s, stderr: %s' % (
            node_name, result.returncode, result.stderr, result.stdout))

    # wait for the node to power-on
    time.sleep(180)

    def _wait_for_node_to_appear():
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node_name))
        metrics_json = resp.json()
        if ('metadata' in metrics_json and
                'state' in metrics_json['metadata'] and
                metrics_json['metadata']['state']['error'] is False):
            return True
        return False

    success = polling2.poll(
        _wait_for_node_to_appear,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for node to reboot'


def poweroff_host_maintenance_mode(request, admin_session,
                                   harvester_api_endpoints):
    host_poweroff = lookup_host_not_harvester_endpoint(request, admin_session,
                                                       harvester_api_endpoints)
    # Enable Maintenance Mode
    resp = admin_session.post(
        host_poweroff['actions']['enableMaintenanceMode'])
    assert resp.status_code == 204, (
        'Failed to update node: %s' % (resp.content))
    node_name = host_poweroff['id']
    poll_for_resource_ready(request, admin_session,
                            harvester_api_endpoints.get_node % (node_name))
    resp = admin_session.get(
        harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert ret_data["spec"]["unschedulable"]
    s = ret_data["metadata"]["annotations"]["harvesterhci.io/maintain-status"]
    assert s in ["running", "completed"]
    node_name = host_poweroff['id']
    # Power Off Node
    power_off_node(request, admin_session, harvester_api_endpoints,
                   node_name)
    resp = admin_session.get(
        harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert "NotReady,SchedulingDisabled" in ret_data["metadata"]["fields"]
    return host_poweroff
