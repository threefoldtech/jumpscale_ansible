#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: network

short_description: A module to add normal and access nodes to the network.

version_added: "1.0.0"

description: A module to add normal and access nodes to the network.

options:
    name:
        description: The network name. Created if it doesn't exist.
        required: true
        type: str
    type:
        description: access|normal
        required: false
        default: normal
        type: str
    identity_name:
        description: The identity instance name registered on the system for the network to be created with.
        required: false
        default: The default identity
        type: str
    pool_id:
        description: The pool id to create the network on.
        required: true
        type: int
    nodes:
        description: A mapping from node ids to ip ranges (range can be anything when adding access). Its length must be one when adding access
        required: true
        type: dict
    ipv4:
        description: The ip version when adding access. Detected automatically when ommited.
        required: false
        type: str

author:
    - Omar Elawady (@OmarElawady)
'''

EXAMPLES = r'''
# Pass in a message
- name: Add a node to the network
  network_node:
    name: management
    pool_id: 34
    nodes:
        26ZATmd3K1fjeQKQsi8Dr7bm9iSRa3ePsV8ubMcbZEuY: 10.100.2.0/24
    identity_name: omar
    type: access
    state: present
'''

RETURN = r'''
changed: False
'''
from jumpscale.loader import j
from jumpscale.clients.explorer.models import NextAction
from ansible.module_utils.basic import AnsibleModule
import traceback
from time import time
import netaddr

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
    raise Exception(f"Failed to add the node to the network in time. Workload id is {wid}")

def wait_until_decommissioned(zos, wid, expiration=3):
    start = time()

    while time() - start < expiration * 60:
        workload = zos.workloads.get(wid)
        if workload.info.next_action == NextAction.DELETED or workload.info.next_action == NextAction.DELETE:
            return True
            
    raise Exception(f"Failed to decmmission wid {wid}")



def is_node_in_network(network, node_id):
    return network.get_node_range(node_id) is not None

def add_network_node(network_name, node_id, ip_range, identity_name, pool_id):
    zos = j.sals.zos.get(identity_name)
    network = zos.network.load_network(network_name)
    if is_node_in_network(network, node_id):
        return False
    if network is None:
        raise Exception(f"The network {network_name} doesn't exist")
    zos.network.add_node(network, node_id, ip_range, pool_id)
    update_network(zos, network)
    return True

def get_network_range(subnet):
    network = netaddr.IPNetwork(subnet)
    return str(network.supernet(16)[0])

def add_network_nodes(network_name, nodes, identity_name, pool_id):
    changed = False
    zos = j.sals.zos.get(identity_name)
    network = zos.network.load_network(network_name)
    if network is None:
        ip_range = get_network_range(list(nodes.values())[0])
        network = zos.network.create(ip_range, network_name)
    for node_id, ip_range in nodes.items():
        if is_node_in_network(network, node_id):
            continue
        changed = True
        zos.network.add_node(network, node_id, ip_range, pool_id)
    update_network(zos, network)
    return changed

def is_node_ipv4(node_id):
    zos = j.sals.zos.get()
    return zos.nodes_finder.filter_public_ip4(zos._explorer.nodes.get(node_id))

def add_network_access(network_name, nodes, identity_name, ipv4):
    node_id, ip_range = list(nodes.items())[0]
    ipv4 = ipv4 or is_node_ipv4(node_id)
    zos = j.sals.zos.get(identity_name)
    network = zos.network.load_network(network_name)
    if not network:
        raise Exception("You have to create the network and add the node to it before making it an access node.")
    if not is_node_in_network(network, node_id):
        raise Exception("You have to add the node to the network before adding it as an access node.")
    if network is None:
        raise Exception(f"The network {network_name} doesn't exist")
    wg_config = zos.network.add_access(network, node_id, ip_range, ipv4=ipv4)
    update_network(zos, network)
    return wg_config

def update_network(zos, network):
    wids = []
    for network_resource in network.network_resources:
        wids.append(zos.workloads.deploy(network_resource))
    for wid in wids:
        wait_until_deployed(zos, wid)

def decommission_workloads(zos, wids):
    for wid in wids:
        zos.workloads.decomission(wid)
    for wid in wids:
        wait_until_decommissioned(zos, wid)

def delete_network_nodes(network_name, nodes, identity_name):
    changed = False
    zos = j.sals.zos.get(identity_name)
    network = zos.network.load_network(network_name)
    if network is None:
        return False
    wids = []
    for node_id, _ in nodes.items():
        if is_node_in_network(network, node_id):
            changed = True
            wids += zos.network.delete_node(network, node_id)
    decommission_workloads(zos, wids)
    update_network(zos, network)
    return changed


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        nodes=dict(type='dict', required=True),
        pool_id=dict(type='int', required=False),
        type=dict(type='str', default='normal'),
        state=dict(type='str', default='present'),
        ipv4=dict(type="bool", required=False),
        identity_name=dict(type='str', required=False),
    )

    result = dict(
        changed=False,
        wg_config=""
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        mutually_exclusive=[
            ['type', 'state']
        ]
    )
        
    name = module.params.get('name')
    type = module.params.get('type')
    pool_id = module.params.get('pool_id')
    identity_name = module.params.get('identity_name')
    state = module.params.get('state')
    nodes = module.params.get('nodes')
    
    if type == "access" and len(nodes) != 1:
        module.fail_json(msg="You can add access to exactly one node.", **result)
        
    if identity_name and j.core.identity.find(identity_name) is None:
        module.fail_json(msg='Identity not registered, please use the identity module to add this identity', **result)
    try:
        if state == 'absent':
            if type == 'access':
                raise Exception("Deleting access is not supported. Only normal nodes can be removed.")
            else:
                result['changed'] = delete_network_nodes(name, nodes, identity_name)
        else:
            if type == "normal":
                if pool_id is None:
                    raise Exception("Missing required value pool_id when adding a node")
                result["changed"] = add_network_nodes(name, nodes, identity_name, pool_id)
            elif type == "access":
                result["wg_config"] = add_network_access(name, nodes, identity_name, pool_id)
                result["changed"] = True
            else:
                raise Exception(f"Unrecognized type: {type}. Types allowed are \"normal\" and \"access\"")
    except Exception:
        module.fail_json(msg=traceback.format_exc(), **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
