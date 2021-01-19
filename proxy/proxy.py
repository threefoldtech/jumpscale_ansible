#!/usr/bin/python

DOCUMENTATION = r'''
---
module: TCP Reverse Proxy

short_description: TCP Reverse Proxy module is responsible for managing tcp reverse proxies workloads on tf farms gateways
                   currently creating subdomain is only supported

version_added: "1.0.0"

description: TCP Reverse Proxy module is responsible for managing tcp reverse proxies workloads on tf farms gateways
             currently creating subdomain is only supported


options:
    state:
        description: state of the specified proxy
        required: true
        type: str
        choices: present (to be extended)
    pool:
        description: id of the pool to choose gateway on
        required: true
        type: int
    gateway:
        description: id of the gateway where the reverse proxy is configured
        required: true
        type: str
    domain:
        description: domain that will be proxied
        required: true
        type: str
    trc_secret:
        description: trc secret to identity the incoming connection from TCP router client
        required: false
        type: str
    identity_name:
        description: identity instance name (if not provided will use the default identity)
        required: false
        type: str
    description:
        description: description of the proxy workload
        required: false
        type: str
    metadata:
        description: metadata of the proxy workload
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
- name: "Test create proxy"
    proxy:
        state: present
        pool: 185
        gateway: 9PdutHsdDSxcKUUyDg8ovS1KWh47qLT5R9h5uoFgRUH2
        domain: asamir-subdomaintest-asamir.webg1test.grid.tf
        trc_secret: "12345678"
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
        domain=dict(type='str', required=True),
        trc_secret=dict(type='str', required=True),
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
    

    identity_name = module.params.get('identity_name', j.core.identity.me.instance_name)
    zos = j.sals.zos.get(identity_name)

    gateway_id = module.params['gateway']
    pool_id = module.params['pool']
    domain = module.params['domain']
    trc_secret = module.params['trc_secret']
    description = module.params['description']
    metadata = module.params['metadata']

    workload = zos.gateway.tcp_proxy_reverse(gateway_id, domain, trc_secret, pool_id)
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

