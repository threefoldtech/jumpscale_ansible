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
        description: identity name to be used to fetch the network. defaults to j.core.identity.me
        required: False
        type: str
    network_name:
        description: name of the network to query
        required: True
        type: str
    node_id:
        description: id of the node in case the operation is get_free_ip
        required: False
        type: str
    operation:
        description: name of the operation/query to perform
        required: True
        type: str
        choices: [get_ip, get_free_range, get_public_ip]
    fact_name:
        description: name of the fact to store the result at. in case of get_ip operation, default is (ip_address) and for get_free_range, default is (ip_range)
        required: False
        type: str
    excluded_ranges:
        description: list of ip ranges to exclude when querying for a free range
        required: True
        type: list
        default: []
    excluded_addresses:
        description: list of ip address to exclude when querying for a free ip address on a node
        required: True
        type: list
        default: []
    farm_name:
        description: name of the farm to search for public ips
        required: False
        type: str


author:
    - Maged Motawea (@m-motawea)
    
'''


RETURN = r'''
ansible_facts:
    description: contains the nodes in the query name.
    type: dict
    returned: always
    sample: "{'ip_address': 10.200.1.224}"
'''



def run_module():
    module_args = dict(
        identity_name=dict(type='str', required=False),
        network_name=dict(type='str', required=False),
        node_id=dict(type='str', required=False),
        excluded_ranges=dict(type='list', required=False, default=[]),
        excluded_addresses=dict(type='list', required=False, default=[]),
        farm_name=dict(type='str', required=False),
        operation=dict(type='str', required=True, choices=["get_ip", "get_free_range", "get_public_ips"]),
        fact_name=dict(type='str', required=False)
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    zos = j.sals.zos.get(module.params['identity_name'])
    if module.params["operation"] == "get_ip":
        network = zos.network.load_network(module.params["network_name"])
        fact_name = module.params["fact_name"] or "ip_address"
        if module.params["excluded_addresses"]:
            network.used_ips += module.params["excluded_addresses"]
        try:
            free_ip = network.get_free_ip(
                node_id=module.params["node_id"]
            )
        except j.exceptions.Input:
            module.fail_json(msg=f"node: {module.params['node_id']} os not part of network: {module.params['network_name']}")
        if not free_ip:
            module.fail_json(msg=f"no free ip available on nodes: {module.params['node_id']}")
        result["ansible_facts"] = {fact_name: free_ip}
    elif module.params["operation"] == "get_free_range":
        network = zos.network.load_network(module.params["network_name"])
        fact_name = module.params["fact_name"] or "ip_range"
        free_range = network.get_free_range(*module.params["excluded_ranges"])
        if not free_range:
            module.fail_json(msg=f"no available ip subnets in network: {module.params['network_name']}")
        result["ansible_facts"] = {fact_name: free_range}
    elif module.params["operation"] == "get_public_ips":
        fact_name = module.params["fact_name"] or "public_ips"
        farm = zos._explorer.farms.get(farm_name=module.params["farm_name"])
        free_addresses = list(filter(lambda address: address.reservation_id == 0, farm.ipaddresses))
        if not free_addresses:
            module.fail_json(msg=f"no free public ips available on farm {farm.name}")
        random.shuffle(free_addresses)
        result["ansible_facts"] = {fact_name: [address.address for address in free_addresses]}

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()

