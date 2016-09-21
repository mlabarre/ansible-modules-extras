#!/usr/bin/python

# Copyright (c) 2016 Helicom
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from distutils.version import StrictVersion


DOCUMENTATION = '''
---
module: os_api_endpoint
short_description: Create, update or delete API endpoints.
extends_documentation_fragment: openstack
author: "Michel Labarre (@mlabarre)"
version_added: "2.2"
description:
    - Add, update or delete API endpoints.
    - V2.0 and V3 API version are supported. So arguments as interface,
      url, public_url, admin_url and internal_url are supported. But
        - for V2 version, only public_url, internal_url and admin_url
          can be specified (not interface, neither url).
        - for V3 version, only interface AND url can be specified
          (no public_url, internal_url and admin_url).
options:
   service_name:
     description:
        - Name for the target service (ie 'keystone', etc.).
     required: true
   service_type:
     description:
        - type for the target service (ie 'identity', etc.).
     required: true
   interface:
     description:
        - Endpoint type (ie 'public', 'internal', 'admin') (v3 format).
     required: false
   url:
     description:
        - Endpoint URL (v3 format).
     required: false
   public_url:
     description:
        - Public endpoint URL (v2 format).
     required: true
   internal_url:
     description:
        - Internal endpoint URL (v2 format).
     required: false
   admin_url:
     description:
        - Admin endpoint URL (v2 format).
     required: false
   region:
     description:
        - Region name or id.
     required: false
   enabled:
     description:
        - Enable endpoint.
     required: false
     default: true
   state:
     description:
       - Should the endpoint be present or absent on the user.
     choices: [present, absent]
     default: present
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Some examples contain a 'cloud' attribute.
# This attribute is not required if you work always with the same API version.

# Add/Update an endpoint internal url with v3 version
- os_keystone_endpoint:
    cloud: cloud_v3_api
    service_name: keystone
    service_type: identity
    interface: internal
    region: myregion
    enabled: True
    url: "http://server:5000/v3"
    state: present

# Add all endpoints public, admin, internal
- os_keystone_endpoint:
    cloud: cloud_v3_api
    service_name: keystone
    service_type: identity
    interface: "{{ item.interface }}"
    url: "{{ item.interface }}"
    region: "{{ item.region }}"
    enabled: "{{ item.enabled }}"
    state: present
  with_items:
    - { interface: 'public', url: 'http://server:5000',
        region: 'myregion', enabled: true }
    - { interface: 'internal', url: 'http://server:5000',
        region: 'myregion', enabled: true }
    - { interface: 'admin', url: 'http://server:35357',
        region: 'myregion', enabled: true }

# Add/Update an endpoint with v2.0 version
- os_keystone_endpoint:
    cloud: cloud_v2_api
    service_name: keystone
    service_type: identity
    public_url: "http://server:5000/v2.0"
    internal_url: "http://server:5000/v2.0"
    admin_url: "http://server:35357/v2.0"
    region: myregion
    state: present

# Remove an endpoint with v3 version
- os_keystone_endpoint:
    cloud: cloud_v3_api
    service_name: keystone
    service_type: identity
    interface_type: internal
    url: "http://internal:5000"
    region: myregion
    state: absent

# Remove an endpoint with v2 version
- os_keystone_endpoint:
    service_name: keystone
    service_type: identity
    public_url: "http://server:5000/v2.0"
    internal_url: "http://server:5000/v2.0"
    admin_url: "http://server:35357/v2.0"
    region: myregion
    state: absent

'''

RETURN = '''
#
'''

def get_endpoint(service, interface):
    """
    Retrieve existing endpoint(s) depending on service and interface values.
    :param service: Service id.
    :param interface: Interface (will be None with v2.0).
    :return: Endpoint entry.
    """
    if interface:
        endpoints_list = cloud.search_endpoints(
            filters={'service_id': service, 'interface': interface})
    else:
        endpoints_list = cloud.search_endpoints(
            filters={'service_id': service})
    if len(endpoints_list) > 1:
        module.fail_json(msg='Multiple endpoint entries exist service %s.'
                             % service)
    return endpoints_list[0] if len(endpoints_list) == 1 else None


def main():

    global cloud, module

    argument_spec = openstack_full_argument_spec(
        service_name=dict(required=True),
        service_type=dict(required=True),
        interface=dict(required=False),
        url=dict(required=False),
        admin_url=dict(required=False),
        public_url=dict(required=False),
        internal_url=dict(required=False),
        region=dict(required=False),
        enabled=dict(default=True, required=False),
        state=dict(default='present', choices=['absent', 'present'])
    )

    module_kwargs = openstack_module_kwargs(
        required_one_of=[
            ['url', 'admin_url', 'internal_url', 'public_url']
        ],
        mutually_exclusive=[
            ['url', 'admin_url'],
            ['url', 'internal_url'],
            ['url', 'public_url'],
        ],
        required_together=[['interface', 'url']]
    )

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)
    # role grant/revoke API introduced in 1.11.0
    if not HAS_SHADE or \
            (StrictVersion(shade.__version__) < StrictVersion('1.11.0')):
        module.fail_json(msg='shade 1.11.0 or higher is required for this module')

    try:

        cloud = shade.operator_cloud(**module.params)

        service_name = module.params.get('service_name', None)
        service_type = module.params.get('service_type', None)
        interface = module.params.get('interface', None)
        url = module.params.get('url', None)
        region = module.params.get('region', None)
        enabled = "True" == module.params.get('enabled', True)
        state = module.params.get('state', None)
        admin_url = module.params.get('admin_url', None)
        internal_url = module.params.get('internal_url', None)
        public_url = module.params.get('public_url', None)

        services_list = cloud.search_services(
            filters={'name': service_name, 'type': service_type})
        if len(services_list) != 1:
            module.fail_json(
               msg='Service %s not found or more than 1 service have this name'
                    % service_name)
        # Only service id is capable to identify unique entry.
        service_id = services_list[0].id

        current_endpoint = get_endpoint(service_id, interface)

        if current_endpoint is None and state == 'absent':
            module.exit_json(changed=False)

        # Check if changes.
        changed = False
        if current_endpoint is None:
            changed = True
        else:
            if url and (enabled is not None
                        and current_endpoint.enabled != enabled):
                changed = True
            if hasattr(current_endpoint, 'region') \
                    and current_endpoint.region != region or \
                    not hasattr(current_endpoint, 'region') \
                    and region is not None:
                changed = True
            if url:
                if current_endpoint.url != url:
                    changed = True
            else:
                if hasattr(current_endpoint, 'internalurl') \
                        and current_endpoint.internalurl != internal_url \
                        or not hasattr(current_endpoint, 'internalurl') \
                        and internal_url is not None:
                    changed = True
                if hasattr(current_endpoint, 'adminurl') \
                        and current_endpoint.adminurl != admin_url \
                        or not hasattr(current_endpoint, 'adminurl') \
                        and admin_url is not None:
                    changed = True
                if hasattr(current_endpoint, 'publicurl') \
                        and current_endpoint.publicurl != public_url \
                        or not hasattr(current_endpoint, 'publicurl') \
                        and public_url is not None:
                    changed = True

        # Handle check mode.
        if module.check_mode:
            if changed and state == "absent":
                changed = False
            module.exit_json(changed=changed)

        args = {}
        for endpoint in ["public_url", "internal_url", "admin_url"]:
            args[endpoint] = module.params.get(endpoint)

        # Do changes.
        if changed:
            if state == "present":
                if current_endpoint is None:
                    cloud.create_endpoint(service_id,
                                          interface=interface,
                                          url=url,
                                          region=region,
                                          enabled=enabled,
                                          **args)
                    changed = True
                else:
                    # Update endpoints.
                    # Shade endpoint update is only possible in API V3.
                    # So we can only use interface, url and region
                    if url:
                        cloud.update_endpoint(current_endpoint.id,
                                              url=url,
                                              interface=interface,
                                              region=region)
                    else:
                        # No update possible in V2.0. So we must delete
                        # and recreate.
                        cloud.delete_endpoint(current_endpoint.id)
                        cloud.create_endpoint(service_id,
                                              interface=interface,
                                              url=url,
                                              region=region,
                                              enabled=enabled,
                                              **args)
            else:
                changed = False
        else:
            if state == 'absent':
                cloud.delete_endpoint(current_endpoint.id)
                changed = True

        module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()
