#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: TCP Reverse Proxy

short_description: TCP Reverse Proxy module is responsible for managing tcp reverse proxies workloads on tf farms gateways
                   currently creating subdomain is only supported

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
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
        type: dict

# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Ahmed Samir (@AhmedSa-mir)
'''

EXAMPLES = r'''
# create subdomain
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
# These are examples of possible return values, and in general should use other names for return values.
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'OK'
'''

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type='str', required=True, choices=['present']),
        pool=dict(type='int', required=True),
        gateway=dict(type='str', required=True),
        domain=dict(type='str', required=True),
        trc_secret=dict(type='str', required=True),
        identity_name=dict(type='str', required=False),
        description=dict(type='str', required=False),
        metadata=dict(type='dict', required=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    
    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # main functionality of the module
    identity_name = module.params.get('identity_name', j.core.identity.me.instance_name)
    zos = j.sals.zos.get(identity_name)

    gateway_id = module.params['gateway']
    pool_id = module.params['pool']
    domain = module.params['domain']
    trc_secret = module.params['trc_secret']
    description = module.params['description']
    metadata = module.params['metadata']

    try:
        workload = zos.gateway.tcp_proxy_reverse(gateway_id, domain, trc_secret, pool_id)
        if metadata:
            workload.info.metadata = metadata
        if description:
            workload.info.description = description
        wid = zos.workloads.deploy(workload)
        result['message'] = zos.workloads.get(wid).to_dict()
        result['changed'] = True
    except Exception as e:
        result['message'] = str(e)
        module.fail_json(msg='Failed to create proxy', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()


if __name__ == '__main__':
    main()

