#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: network

short_description: A module to add/remove normal and access nodes to the network.

version_added: "1.0.0"

description: A module to add/remove normal and access nodes to the network.

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
    state:
        description: Should the network be created/deleted
        required: false
        default: present
        choices: present|absent
        type: str
author:
    - Omar Elawady (@OmarElawady)
'''

EXAMPLES = r'''
- name: Create a network
  network:
    name: management
    identity_name: omar0
    state: present
- name: Delete a network
  network:
    name: management
    identity_name: omar0
    state: absent
'''

RETURN = r'''
changed: False
'''
from jumpscale.loader import j
from ansible.module_utils.basic import AnsibleModule
from jumpscale.clients.explorer.models import NextAction, WorkloadType
from time import time

def wait_until_decommissioned(zos, wid, expiration=3):
    start = time()

    while time() - start < expiration * 60:
        workload = zos.workloads.get(wid)
        if workload.info.next_action == NextAction.DELETED or workload.info.next_action == NextAction.DELETE:
            return True
            
    raise TimeoutError(f"Failed to decmmission wid {wid}")

def decommission_workloads(zos, wids):
    for wid in wids:
        zos.workloads.decomission(wid)
    for wid in wids:
        wait_until_decommissioned(zos, wid)

def create_network(name, zos, ip_range="10.100.0.0/16"):
    """
    1. Get a pool with at least one up node or create one if non exists.
    2. Get an up node in the pool and add it to the network.
    
    1.1. iterate over all current pools and check if a one with up node is found return it.
    1.2. otherwise, iterate over all farms and make a pool on the farm, then check if the pool contains an up node.
         stop once found.
    """
    pool, node = fetch_pool_with_up_node(zos)
    if pool is None:
        raise Exception("Couldn't find a pool or a farm with up node")
    
    network = zos.network.create(ip_range, name)
    add_node_to_network(network, zos, pool, node)
    update_network(zos, network)

    return True
    
def fetch_pool_with_up_node(zos):
    pool, node = get_pool_with_up_node(zos)
    if pool is None:
        pool, node = create_pool_on_farm_with_up_node(zos)
    return pool, node

def get_pool_with_up_node(zos):
    pools = zos.pools.list()
    for pool in pools:
        node = get_up_node(pool)
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

def create_pool_on_farm_with_up_node(zos):
    farms = zos._explorer.farms.list()
    for farm in farms:
        pool = zos.pools.create(0, 0, 0, farm.name)
        up_node = get_up_node(pool)
        return pool.reservation_id, up_node
    return None, None

def get_up_node(pool):
    node_ids = pool.node_ids
    zos = j.sals.zos.get()
    for node_id in node_ids:
        node = zos._explorer.nodes.get(node_id)
        if zos.nodes_finder.filter_is_up(node):
            return node_id
    return None

def delete_network(name, identity_name):
    identity = j.core.identity.get(identity_name) if identity_name else j.core.identity.me
    zos = j.sals.zos.get(identity_name)
    tid = identity.tid
    workloads = zos.workloads.list(tid, NextAction.DEPLOY)
    network_workloads = []
    for workload in workloads:
        if workload.info.workload_type == WorkloadType.Network_resource and workload.name == name:
            network_workloads.append(workload.id)
    decommission_workloads(zos, network_workloads)
    return network_workloads != []


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
        identity_name=dict(type='str', required=False),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
        
    name = module.params.get('name')
    state = module.params.get('state') or "present"
    identity_name = module.params.get('identity_name')
    zos = j.sals.zos.get(identity_name)
    network = zos.network.load_network(name)
    try:
        if state == "present" and network is None:
            result['changed'] = create_network(name, zos)
        elif state == "absent" and network is not None:
            result['changed'] = delete_network(name, identity_name)
    except Exception as e:
        import traceback
        module.fail_json(f"Operation failed: {str(e)}, {traceback.format_exc()}", **result)
    
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
