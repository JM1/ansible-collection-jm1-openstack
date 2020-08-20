#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:set fileformat=unix shiftwidth=4 softtabstop=4 expandtab:
# kate: end-of-line unix; space-indent on; indent-width 4; remove-trailing-space on;

# Copyright: (c) 2020, Jakob Meng <jakobmeng@web.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---

module: floating_ip

short_description: Allocate/Release floating IP from a OpenStack network

description:
    - "This module allows one to allocate or release an floating ip to a OpenStack network. Returns the floating IP when
       attaching only if I(wait=true). Unlike the official OpenStack Ansible module openstack.cloud.floating_ip, this
       module does allocate floating ips to networks, but does not assign floating ips to servers."

requirements: []

options:
    floating_ip_address:
        description:
            - "An floating IP address to allocate or to release. Required only if I(state) is absent. When I(state) is
               C(present) can be used to specify a IP address."
          to attach.
        required: false
        type: str
    floating_network_name:
        description:
            - "The name or ID of a neutron external network or a nova pool name."
        required: true
        type: str
    project_name:
        description:
            - "The name or ID of the project, defaulting to the current project."
        required: false
        type: str
    state:
        choices: [present, absent]
        default: present
        description:
            - "Should the floating ip be present or absent."
        type: str

notes:
    - "Option I(wait) must be set to C(yes) for the module to return the value of the floating IP address."

extends_documentation_fragment:
  - openstack.cloud.openstack

author: "Jakob Meng (@jm1)"
'''

EXAMPLES = r'''
# Allocate a floating IP
- jm1.openstack.floating_ip:
    cloud: devstack
    floating_network_name: ext_net

# Release a floating IP address
- jm1.openstack.floating_ip:
     cloud: devstack
     floating_ip_address: 203.0.113.2
     floating_network_name: ext_net
     state: absent
'''

RETURN = r'''
floating_ip_address:
    description:
        - "Floating IP address on network I(floating_network_name) in project I(project_name). If I(floating_ip_address)
           has not been set, then it returns the floating ip address that has been created or the first one if a
           floating ip address already exists."
    returned: changed or success
    type: str
    sample: '203.0.113.2'

floating_network_id:
    description: "Id of the floating IP's network"
    returned: changed or success
    type: str
    sample: '1cface9294ba40cc9f22f9101d011f0c'

floating_network_name:
    description: "Name of the floating IP's network"
    returned: changed or success
    type: str
    sample: 'ext_net'

project_id:
    description: "Id of the project to which the floating ip has been allocated to."
    returned: changed or success
    type: str
    sample: '0ebadc9294ba40cc9f22f9101d011d0c'

project_name:
    description: "Name of the project to which the floating ip has been allocated to."
    returned: changed or success
    type: str
    sample: 'devstack'
'''

# NOTE: Synchronize imports with DOCUMENTATION string above
from ansible.module_utils.openstack import (openstack_full_argument_spec, openstack_cloud_from_module)
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
import traceback


def get_project(name_or_id,
                module, sdk, cloud):

    if not name_or_id or name_or_id in [cloud.current_project.name, cloud.current_project.id]:
        project = cloud.current_project
    else:
        project = cloud.get_project(name_or_id=name_or_id)

    if not project:
        raise ValueError('Project %s does not exist' % name_or_id)

    return project


def get_network(name_or_id,
                project_id,
                module, sdk, cloud):

    networks = cloud.search_networks(
        name_or_id=name_or_id,
        filters=({'tenant_id': project_id} if project_id else None))

    if not networks or len(networks) > 1:
        raise ValueError('Network %s is invalid or ambiguous' % name_or_id)

    return networks[0]


def allocate(floating_ip_address,
             floating_network_name,
             project_name,
             state,
             timeout,
             wait,
             module, sdk, cloud):

    project = get_project(project_name, module, sdk, cloud)
    project_name = project.name

    network = get_network(floating_network_name, project.id, module, sdk, cloud)

    fip_filters = {'network': network.id, 'tenant_id': project.id}

    if floating_ip_address:
        fip_filters['floating_ip_address'] = floating_ip_address

    fips = cloud.search_floating_ips(filters=fip_filters)

    if fips:
        # floating ip already exists
        return False, fips[0].floating_ip_address, network.name, network.id, project.name, project.id

    fip = cloud.network.create_ip(
        floating_ip_address=floating_ip_address,
        floating_network_id=network.id,
        tenant_id=project.id,
        timeout=timeout,
        wait=wait)

    return True, fip.floating_ip_address, network.name, network.id, project.name, project.id


def release(floating_ip_address,
            floating_network_name,
            project_name,
            state,
            timeout,
            wait,
            module, sdk, cloud):

    project = get_project(project_name, module, sdk, cloud)
    project_name = project.name

    network = get_network(floating_network_name, project.id, module, sdk, cloud)

    fips = cloud.search_floating_ips(filters={
        'floating_ip_address': floating_ip_address,
        'network': network.id,
        'tenant_id': project.id
    })

    if not fips:
        # floating ip absent already
        return False, floating_ip_address, network.name, network.id, project.name, project.id

    assert len(fips) == 1

    if len(fips) > 1:
        raise ValueError('Floating ip address %s is ambiguous' % floating_ip_address)

    fip = fips[0]

    cloud.network.delete_ip(floating_ip=fip, ignore_missing=False)
    return True, fip.floating_ip_address, network.name, network.id, project.name, project.id


def core(module):
    sdk, cloud = openstack_cloud_from_module(module)

    floating_ip_address = module.params['floating_ip_address']
    floating_network_name = module.params['floating_network_name']
    project_name = module.params['project_name']
    state = module.params['state']
    timeout = module.params['timeout']
    wait = module.params['wait']

    if module.check_mode:
        return dict(
            changed=False,
            floating_ip_address=floating_ip_address,
            floating_network_name=floating_network_name,
            project_name=project_name,
            state=state,
            timeout=timeout,
            wait=wait)

    if state == 'present':
        changed, floating_ip_address, floating_network_name, floating_network_id, project_name, project_id = allocate(
            floating_ip_address,
            floating_network_name,
            project_name,
            state,
            timeout,
            wait,
            module, sdk, cloud)
    elif state == 'absent':
        changed, floating_ip_address, floating_network_name, floating_network_id, project_name, project_id = release(
            floating_ip_address,
            floating_network_name,
            project_name,
            state,
            timeout,
            wait,
            module, sdk, cloud)

    return dict(
        changed=changed,
        floating_ip_address=floating_ip_address,
        floating_network_name=floating_network_name,
        floating_network_id=floating_network_id,
        project_name=project_name,
        project_id=project_id,
        state=state,
        timeout=timeout,
        wait=wait)


def main():
    module = AnsibleModule(
        argument_spec=openstack_full_argument_spec(
            floating_ip_address=dict(type='str', default=None),
            floating_network_name=dict(required=True, type='str', default=None),
            project_name=dict(type='str', default=None),
            state=dict(type='str', choices=['present', 'absent'], default='present')
        ),
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['floating_ip_address']]
        ]
    )

    try:
        result = core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
