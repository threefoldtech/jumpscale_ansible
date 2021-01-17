#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j



DOCUMENTATION = r'''
---
module: public_ip

short_description: public_ip module for zos

version_added: "1.0.0"

description: module to reserve public_ips on TF Grid.

options:
    identity_name:
        description: identity name to be used to deploy the container defaults to j.core.identity.me
        required: False
        type: str
    pool_id:
        description: capacity pool id to deploy the public ip in
        required: True
        type: int
    node_id:
        description: id of the node to deploy the container on
        required: True
        type: str
    ip_address:
        description: the farm ip address to reserve
        required: True
        type: str
    description:
        description: description of the workload
        required: False
        type: str
        default: ""
    metadata:
        description: workload metadata
        required: False
        type: str
        default: ""
    wait:
        description: wait for workload to be successful before exit. defaults to True
        required: False
        type: bool
        default: True
    

author:
    - Maged Motawea (@m-motawea)
    
'''



RETURN = r'''
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
message:
    description: The output message that the test module generates.
    type: dict
    returned: always
    sample: "{'wid': 18116, 'message': ''}"
'''


def run_module():
    module_args = dict(
        identity_name=dict(type='str', required=False),
        pool_id=dict(type='int', required=True),
        node_id=dict(type='str', required=True),
        ip_address=dict(type='str', required=True),
        description=dict(type='str', required=False, default=""),
        metadata=dict(type='str', required=False, default=""),
        # wait for workload flag
        wait=dict(type='bool', required=False, default=True),
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    zos = j.sals.zos.get(module.params['identity_name'])
    ip = zos.public_ip.create(
        node_id=module.params['node_id'],
        pool_id=module.params['pool_id'],
        ipaddress=module.params['ip_address'],
    )
    ip.info.description = module.params['description']
    ip.info.description = module.params['metadata']
    wid = zos.workloads.deploy(ip)

    result["changed"] = True
    result["message"] = {"wid": wid, "message": ""}

    if module.params["wait"]:
        success, msg = zos.workloads.wait(wid)
        result["changed"] = success
        result["message"]["message"] = msg

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
