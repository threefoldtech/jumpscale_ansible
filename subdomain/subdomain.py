#!/usr/bin/python


DOCUMENTATION = r'''
---
module: Subdomain

short_description: Subdomain module is responsible for creating subdomains on tf farms gateways
                   currently creating subdomain is only supported


version_added: "1.0.0"

description: Subdomain module is responsible for creating subdomains on tf farms gateways
             currently creating subdomain is only supported

options:
    state:
        description: state of the specified subdomain
        required: true
        type: str
        choices: present (to be extended)
    pool:
        description: id of the pool to choose gateway on
        required: true
        type: int
    gateway:
        description: id of the node of the gateway to create subdomain on
        required: true
        type: str
    subdomain:
        description: subdomain
        required: true
        type: str
    addresses:
        description: list of addresses the subdomain will point to
        required: false
        type: list
    identity_name:
        description: identity instance name (if not provided will use the default identity)
        required: false
        type: str
    description:
        description: description of the subdomain workload
        required: false
        type: str
    metadata:
        description: metadata of the subdomain workload
        required: false
        type: str
    wait:
        description: wait for workload to be successful before exit. defaults to True
        required: False
        type: bool
        default: True


author:
    - Ahmed Samir (@AhmedSa-mir)
'''

EXAMPLES = r'''
- name: "Test create subdomain"
    subdomain:
        state: present
        pool: 185
        gateway: 9PdutHsdDSxcKUUyDg8ovS1KWh47qLT5R9h5uoFgRUH2
        subdomain: asamir-subdomaintest-asamir.webg1test.grid.tf
        identity_name: asamir_test
        description: "test domain"
        metadata:
          test: "test"
    register: result
'''

RETURN = r'''
wid:
    description: id of the deployed workload.
    type: int
    returned: always
message:
    description: message returned in the workload result in case of failures.
    type: str
    returned: always
'''


from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j

def run_module():
    module_args = dict(
        state=dict(type='str', required=True, choices=['present']),
        pool=dict(type='int', required=True),
        gateway=dict(type='str', required=True),
        subdomain=dict(type='str', required=True),
        addresses=dict(type='list', required=False),
        identity_name=dict(type='str', required=False),
        description=dict(type='str', required=False),
        metadata=dict(type='str', required=False),
        wait=dict(type='bool', required=False, default=True),
    )

    result = dict(
        changed=False,
        message=None,
        wid=None,
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )
    
    if module.check_mode:
        module.exit_json(**result)

    identity_name = module.params.get('identity_name', j.core.identity.me.instance_name)
    zos = j.sals.zos.get(identity_name)

    gateway_id = module.params['gateway']
    pool_id = module.params['pool']
    subdomain = module.params['subdomain']
    addresses = module.params['addresses']
    description = module.params['description']
    metadata = module.params['metadata']
    if not addresses:
        gateway = j.core.identity.me.explorer.gateway.get(gateway_id)
        addresses = [j.sals.nettools.get_host_by_name(ns) for ns in gateway.dns_nameserver]

    workload = zos.gateway.sub_domain(gateway_id, subdomain, addresses, pool_id)
    if metadata:
        workload.info.metadata = metadata
    if description:
        workload.info.description = description
    wid = zos.workloads.deploy(workload)
    result["changed"] = True
    result.update({"wid": wid, "message": ""})

    if module.params["wait"]:
        success, msg = zos.workloads.wait(wid)
        result["changed"] = success
        result["message"] = msg
        if not success:
            module.fail_json(msg=msg, **result)

    module.exit_json(**result)

def main():
    run_module()


if __name__ == '__main__':
    main()

