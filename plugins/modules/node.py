#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j


DOCUMENTATION = r'''
---
module: node

short_description: Node module for get node info from zos

version_added: "1.0.0"

description: module to get nodes data from zos.

options:
    identity_name:
        description: identity name to be used to search. defaults to j.core.identity.me
        required: False
        type: str
    node_id:
        description: node id to search
        required: False
        type: str
    gateway:
        description: If gateway node
        required: False
        type: bool
        default: False
    
author:
    - Mahmoud Ayoub (@dmahmouali)
    
'''



RETURN = r'''
ansible_facts:
    description: contains the nodes in the query name.
    type: dict
    returned: always
    sample: "{'node_id': ['FED1ZsfbUz3jcJzzqJWyGaoGC61bdN8coKJNte96Fo7k']}"
'''


def run_module():
    module_args = dict(
        identity_name=dict(type='str', required=False),
        node_id=dict(type='str', required=True),
        gateway=dict(type='bool', required=False, default=False),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    zos = j.sals.zos.get(module.params['identity_name'])
    node = None
    
    try:
        if module.params["gateway"]:
            node = zos.gateways_finder._gateway.get(module.params["node_id"])
        else:
            node = zos.nodes_finder._nodes.get(module.params["node_id"])
    except Exception as e:
        module.fail_json(msg=f"{str(e)},\n{module.params}")
    
    
    result["ansible_facts"] = {module.params["node_id"]: node.to_dict()}

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
