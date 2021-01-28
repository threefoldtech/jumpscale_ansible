#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: network

short_description: A module to add access to a network.

version_added: "1.0.0"

description: A module to add access to a network.

options:
    name:
        description: The network name.
        required: true
        type: str
    identity_name:
        description: The identity instance name registered on the system for the network to be created with.
        required: false
        default: The default identity
        type: str
    ipv4:
        description: The ip version when adding access. Detected automatically when ommited.
        required: false
        type: bool
        default: false

author:
    - Omar Elawady (@OmarElawady)
'''

EXAMPLES = r'''
# Pass in a message
- name: Add a node to the network
  network_node:
    name: management
    identity_name: omar
    ipv4: true
'''

RETURN = r'''
changed: False
wg_config: "config"
'''
from jumpscale.loader import j
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.threefold.jsgrid.plugins.module_utils.network import is_node_in_network, add_node_to_network, update_network
from time import time

def add_network_access(network, zos, ipv4):
    access_filter = zos.nodes_finder.filter_public_ip6
    if ipv4:
        access_filter = zos.nodes_finder.filter_public_ip4
    pool_id, node_id = fetch_pool_with_access_node(zos, access_filter)
    if pool_id is None:
        raise Exception("Couldn't find a pool or a farm with access node of the specified type")
    add_node_to_network(network, zos, pool_id, node_id)
    wg_config = zos.network.add_access(network, node_id, network.get_free_range(), ipv4=ipv4)
    update_network(zos, network)
    return wg_config


def fetch_pool_with_access_node(zos, access_filter):
    pool, node = get_pool_with_access_node(zos, access_filter)
    if pool is None:
        pool, node = create_pool_on_farm_with_access_node(zos, access_filter)
    return pool, node

def get_pool_with_access_node(zos, access_filter):
    pools = zos.pools.list()
    for pool in pools:
        node = get_access_node(pool, access_filter)
        if node:
            return pool.pool_id, node
    return None, None

def update_network(zos, network):
    wids = []
    for network_resource in network.network_resources:
        wids.append(zos.workloads.deploy(network_resource))
    for wid in wids:
        wait_until_deployed(zos, wid)

def wait_until_deployed(zos, wid, expiration=3):
    start = time()

    while time() - start < expiration * 60:
        workload = zos.workloads.get(wid)
        if workload.info.result.workload_id:
            success = workload.info.result.state.value == 1
            if success:
                return True
            else:
                error_message = workload.info.result.message
                raise Exception(f"Failed to add node with workload id {wid} to the network due to the error: {error_message}")    
    raise TimeoutError(f"Failed to add the node to the network in time. Workload id is {wid}")

def add_node_to_network(network, zos, pool, node):
    node_ip_range = network.get_free_range()
    zos.network.add_node(network, node, node_ip_range, pool)

def create_pool_on_farm_with_access_node(zos, access_filter):
    farms = zos._explorer.farms.list()
    for farm in farms:
        pool = zos.pools.create(0, 0, 0, farm.name)
        access_node = get_access_node(pool, access_filter)
        return pool.reservation_id, access_node
    return None, None

def get_access_node(pool, access_filter):
    node_ids = pool.node_ids
    zos = j.sals.zos.get()
    for node_id in node_ids:
        node = zos._explorer.nodes.get(node_id)
        if zos.nodes_finder.filter_is_up(node) and access_filter(node):
            return node_id
    return None


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        identity_name=dict(type='str', required=False),
        ipv4=dict(type="bool", required=False, default=False),
    )

    result = dict(
        changed=True,
        wg_config=""
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
        
    name = module.params.get('name')
    identity_name = module.params.get('identity_name')
    ipv4 = module.params.get('ipv4')
    
    zos = j.sals.zos.get(identity_name)
    network = zos.network.load_network(name)

    if network is None:
        module.fail_json('The network specified doesn\'t exist', **result)
    try:
        result['wg_config'] = add_network_access(network, zos, ipv4)
    except Exception as e:
        import traceback
        module.fail_json(f"Operation failed: {str(e)}, {traceback.format_exc()}", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
