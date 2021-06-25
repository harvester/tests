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
import os
import polling2
import random
import string
import uuid


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


def poll_for_resource_ready(admin_session, endpoint, expected_code=200):
    ready = polling2.poll(
        lambda: admin_session.get(endpoint).status_code == expected_code,
        step=5,
        timeout=60)
    assert ready, 'Timed out while waiting for %s to yield %s' % (
        endpoint, expected_code)


def get_latest_resource_version(admin_session, lookup_endpoint):
    poll_for_resource_ready(admin_session, lookup_endpoint)
    resp = admin_session.get(lookup_endpoint)
    assert resp.status_code == 200, 'Failed to lookup resource: %s' % (
        resp.content)
    return resp.json()['metadata']['resourceVersion']


def poll_for_update_resource(admin_session, update_endpoint, request_json,
                             lookup_endpoint):

    resp = None

    def _update_resource():
        # we want the update response to return back to the caller
        nonlocal resp

        # first we need to get the latest resourceVersion and fill that in
        # the request_json as it is a required field and must be the latest.
        request_json['metadata']['resourceVersion'] = (
            get_latest_resource_version(admin_session, lookup_endpoint))
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
