#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: network

short_description: A module to add/remove nodes to the network.

version_added: "1.0.0"

description: A module to add/remove nodes to the network.

options:
    name:
        description: The network name. Created if it doesn't exist.
        required: true
        type: str
    identity_name:
        description: The identity instance name registered on the system for the network to be created with.
        required: false
        default: The default identity
        type: str
    nodes:
        description: The nodes ids of the nodes to be added/removed
        required: true
        type: list
    state:
        description: Should the node be added/deleted
        required: false
        default: present
        choices: present|absent
        type: str

author:
    - Omar Elawady (@OmarElawady)
'''

EXAMPLES = r'''
# Pass in a message
- name: Add a node to the network
  network_node:
    name: management
    nodes:
        - 26ZATmd3K1fjeQKQsi8Dr7bm9iSRa3ePsV8ubMcbZEuY
        - BSusuRh6qFzheQFwNPe1S5FA5pdSZVJwVLhpNS6GN4XD
    identity_name: omar
    state: present
'''

RETURN = r'''
changed: False
wg_config: "config" # in case of adding access
'''
from jumpscale.loader import j
from jumpscale.clients.explorer.models import NextAction
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.threefold.jsgrid.plugins.module_utils.network import is_node_in_network, add_node_to_network, update_network
from ansible_collections.threefold.jsgrid.plugins.module_utils.workloads import decommission_workloads
from time import time
import netaddr

def create_pool_node_mapping(zos):
    pools = zos.pools.list()
    node_pool = {}
    for pool in pools:
        for node_id in pool.node_ids:
            node_pool[node_id] = pool.pool_id
    return node_pool

def create_pool_with_node(zos, node_id):
    node = zos._explorer.nodes.get(node_id)
    farm_id = node.farm_id
    farm = zos._explorer.farms.get(farm_id)
    farm_name = farm.name
    pool = zos.pools.create(0, 0, 0, farm_name)
    return pool.reservation_id

def add_nodes_to_network(network, zos, nodes):
    node_pool = create_pool_node_mapping(zos)
    changed = False
    for node_id in nodes:
        if is_node_in_network(network, node_id):
            continue
        changed = True
        if node_id in node_pool:
            pool_id = node_pool[node_id]
        else:
            pool_id = create_pool_with_node(zos, node_id)
        add_node_to_network(network, zos, pool_id, node_id)
    if changed:
        update_network(zos, network)
    return changed

def delete_nodes_from_network(network, zos, nodes):
    changed = False
    wids = []
    for node_id in nodes:
        if is_node_in_network(network, node_id):
            changed = True
            wids += zos.network.delete_node(network, node_id)
    decommission_workloads(zos, wids)
    update_network(zos, network)
    return changed

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        nodes=dict(type='list', required=True),
        identity_name=dict(type='str', required=False),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    result = dict(
        changed=False
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
        
    name = module.params.get('name')
    nodes = module.params.get('nodes')
    identity_name = module.params.get('identity_name')
    state = module.params.get('state')
    
    zos = j.sals.zos.get(identity_name)
    network = zos.network.load_network(name)
    
    if network is None:
        module.fail_json('The network specified doesn\'t exist', **result)
    try:
        if state == 'present':
            result['changed'] = add_nodes_to_network(network, zos, nodes)
        else:
            result['changed'] = delete_nodes_from_network(network, zos, nodes)
    except Exception as e:
        import traceback
        module.fail_json(f"Operation failed: {str(e)}, {traceback.format_exc()}", **result)
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
