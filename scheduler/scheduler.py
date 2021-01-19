#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j
import random



DOCUMENTATION = r'''
---
module: scheduler

short_description: scheduler module for zos

version_added: "1.0.0"

description: module to automatically select nodes on the tfgrid.

options:
    identity_name:
        description: identity name to be used to search. defaults to j.core.identity.me
        required: False
        type: str
    pool_id:
        description: capacity pool id to search int
        required: False
        type: int
    farm_id:
        description: id of the farm to search int
        required: False
        type: int
    farm_name:
        description: name of the farm to search int
        required: False
        type: str
    country:
        description: country where the nodes are located
        required: False
        type: str
    city:
        description: city where the nodes are located
        required: False
        type: str
    cru:
        description: how much free cru on the node
        required: False
        type: int
    mru:
        description: how much free mru on the node
        required: False
        type: int
    sru:
        description: how much free sru on the node
        required: False
        type: int
    hru:
        description: how much free hru on the node
        required: False
        type: int
    ip_version:
        description: ip version available on the node
        required: False
        type: str
        choices: [ipv4, ipv6]
    public_ip:
        description: specify the nodes can be used to deploy public ip workloads
        required: False
        type: bool
    no_nodes:
        description: how many nodes to select
        required: False
        type: int
        default: 1
    query_name:
        description: used as a key to ansible fact containing the result node_ids
        required: False
        type: str
        default: selected_nodes
    excluded_nodes:
        description: excludes the specified node ids from search
        required: False
        type: list
    randomize:
        description: to randomize the result returned instead of using the same order as returned from explorer
        required: False
        type: bool
        default: True


author:
    - Maged Motawea (@m-motawea)
    
'''



RETURN = r'''
ansible_facts:
    description: contains the nodes in the query name.
    type: dict
    returned: always
    sample: "{'selected_nodes': ['FED1ZsfbUz3jcJzzqJWyGaoGC61bdN8coKJNte96Fo7k']}"
'''


def run_module():
    module_args = dict(
        identity_name=dict(type='str', required=False),
        pool_id=dict(type='int', required=False),
        farm_id=dict(type='int', required=False),
        farm_name=dict(type='str', required=False),
        country=dict(type='str', required=False),
        city=dict(type='str', required=False),
        cru=dict(type='int', required=False),
        mru=dict(type='int', required=False),
        sru=dict(type='int', required=False),
        hru=dict(type='int', required=False),
        ip_version=dict(type='str', required=False, choices=["ipv4", "ipv6"]),
        public_ip=dict(type='bool', required=False),
        no_nodes=dict(type='int', required=False, default=1),
        query_name=dict(type='str', required=False, default="selected_nodes"),
        excluded_nodes=dict(type='list', required=False, default=[]),
        randomize=dict(type='bool', required=False, default=True),
        gateway=dict(type='bool', required=False, default=False),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    zos = j.sals.zos.get(module.params['identity_name'])

    filters = [zos.nodes_finder.filter_is_up, lambda node: node.node_id not in module.params["excluded_nodes"]]
    if not module.params["gateway"]:
        if module.params["ip_version"] == "ipv4":
            filters.append(zos.nodes_finder.filter_public_ip4)
        elif module.params["ip_version"] == "ipv6":
            filters.append(zos.nodes_finder.filter_public_ip6)
        if module.params["public_ip"]:
            filters.append(zos.nodes_finder.filter_public_ip_bridge)

        nodes = zos.nodes_finder.nodes_by_capacity(
            farm_id=module.params["farm_id"],
            farm_name=module.params["farm_name"],
            country=module.params["country"],
            city=module.params["city"],
            cru=module.params["cru"],
            mru=module.params["mru"],
            sru=module.params["sru"],
            hru=module.params["hru"],
            pool_id=module.params["pool_id"],
        )
    else:
        nodes = zos.gateways_finder.gateways_search(
            country=module.params["country"],
            city=module.params["city"],
        )
        if module.params["pool_id"]:
            pool = zos.pools.get(module.params["pool_id"])
            filters.append(
                lambda node: node.node_id in pool.node_ids
            )
        farm_id = module.params["farm_id"]
        if not farm_id and module.params["farm_name"]:
            farm_id = zos._explorer.farms.get(farm_name=module.params["farm_name"])
        if farm_id:
            filters.append(lambda node: node.farm_id == farm_id)

    nodes = list(filter(lambda node: all(f(node) for f in filters), nodes))
    if len(nodes) < module.params["no_nodes"]:
        module.fail_json(msg=f"not enough nodes to satisfy query {module.params}")
    if module.params["randomize"]:
        random.shuffle(nodes)
    result["ansible_facts"] = {module.params["query_name"]: [node.node_id for node in nodes[:module.params["no_nodes"]]]}

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
