#!/usr/bin/python

# Copyright: (c) 2020, Your Name <YourName@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: jsgrid_network

short_description: A module to add and remove a network

version_added: "1.0.0"

description: This is my longer description explaining my test info module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.netowrk_info:
    name: hello world
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
my_useful_info:
    description: The dictionary containing information about your system.
    type: dict
    returned: always
    sample: {
        'foo': 'bar',
        'answer': 42,
    }
'''

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j
from jumpscale.clients.explorer.models import NextAction, WorkloadType
import traceback
from time import time
from requests.exceptions import HTTPError
import netaddr

def network_exists(zos, name):
    return zos.network.load_network(name) is not None

def assert_created(zos, name, expiration):
    start = time()
    while time() - start < expiration * 60:
        if network_exists(zos, name):
            return True
    raise Exception("Network wasn't created on time")
    
def assert_removed(zos, name, expiration):
    start = time()
    while time() - start < expiration * 60:
        if not network_exists(zos, name):
            return True
    raise Exception("Network wasn't removed on time")

def fetch_pool_node(zos, pool_id):
    pool = zos._explorer.pools.get(pool_id)
    node_ids = pool.node_ids
    for node_id in node_ids:
        try:
            node = zos._explorer.nodes.get(node_id)
            if zos.nodes_finder.filter_is_up(node):
                return node_id
        except HTTPError:
            pass
    raise Exception("node_id not provided and no nodes are up in the provided pool")


def create_network(identity_name, name, pool_id, ip_range, node_id, node_ip_range):
    identity_name = identity_name or j.core.identity.me.instance_name
    zos = j.sals.zos.get(identity_name)
    ip_range = ip_range or "10.100.0.0/16"
    node_ip_range = node_ip_range or str(next(netaddr.IPNetwork(ip_range).subnet(24)))
    node_id = node_id or fetch_pool_node(zos, pool_id)
    if network_exists(zos, name):
        return False
    network = zos.network.create(ip_range, name)
    zos.network.add_node(network, node_id, node_ip_range, pool_id)
    zos.workloads.deploy(network.network_resources[0])
    assert_created(zos, name, 3)
    return True

def remove_network(identity_name, name):
    identity_name = identity_name or j.core.identity.me.instance_name
    zos = j.sals.zos.get(identity_name)
    if not network_exists(zos, name):
        return False
    network = zos.network.load_network(name)
    for w in network.network_resources:
        zos.workloads.decomission(w.id)
    assert_removed(zos, name, 3)
    return True

def validate_creation_fields(module, result):
    if module.params['pool_id'] is None:
        module.fail_json(msg="missing required argument pool_id for network creation", **result)

# name, access_node, ip_range, ip_version, pool_id, identity_name=None
def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', required=True),
        identity_name=dict(type='str', required=False),
        pool_id=dict(type='int', required=False),
        node_id=dict(type='str', required=False),
        node_ip_range=dict(type='str', required=False),
        ip_range=dict(type='str', required=False)
    )
    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    name = module.params.get('name')
    pool_id = module.params.get('pool_id')
    ip_range = module.params.get('ip_range')
    node_ip_range = module.params.get('node_ip_range')
    identity_name = module.params.get('identity_name')
    state = module.params.get('state')
    node_id = module.params.get('node_id')
    if identity_name and j.core.identity.find(identity_name) is None:
        module.fail_json(msg='Identity not registered, please use the identity module to add this identity', **result)
    zos = j.sals.zos.get(identity_name)
    try:
        if state == 'present':
            validate_creation_fields(module, result)
            result['changed'] = create_network(identity_name, name, pool_id, ip_range, node_id, node_ip_range)
        elif state == 'removed':
            result['changed'] = remove_network(identity_name, name)
    except Exception as e:
        module.fail_json(msg=traceback.format_exc(), **result)


    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
