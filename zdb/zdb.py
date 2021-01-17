#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: ZDB

short_description: ZDB module is responsible for managing ZDBs. Currently creating ZDB is only supported.

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: ZDB module is responsible for managing ZDBs. Currently creating ZDB is only supported.

state=dict(type='str', required=True, choices=['present']),
        pool=dict(type='int', required=True),
        node=dict(type='str', required=True),
        size=dict(type='str', required=True),
        mode=dict(type='str', required=True),
        password=dict(type='str', required=True),
        disk_type=dict(type='str', required=False),
        identity_name=dict(type='str', required=False),
    )

options:
    state:
        description: state of the specified ZDB
        required: true
        type: str
        choices: present (to be extended)
    pool:
        description: id of the pool to deploy ZDB on
        required: true
        type: int
    node:
        description: id of the node to deploy ZDB on
        required: true
        type: int
    size:
        description: size of the ZDB in GiB
        required: true
        type: int
    mode:
        description: ZDB mode (SEQ or USER)
        required: true
        type: str
        choices: SEQ, USER
    password:
        description: ZDB password (no password == "")
        required: true
        type: str
    disk_type:
        description: disk type used in ZDB (SSD or HDD)
        required: false
        type: str
        choices: SSD, HDD
        default: SSD
    identity_name:
        description: identity instance name (if not provided will use the default identity)
        required: false
        type: str

# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Ahmed Samir (@AhmedSa-mir)
'''

EXAMPLES = r'''
# create subdomain
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
        node=dict(type='str', required=True),
        size=dict(type='int', required=True),
        mode=dict(type='str', required=True, choices=['SEQ', 'USER']),
        password=dict(type='str', required=True),
        disk_type=dict(type='str', required=False, choices=['SSD', 'HDD'], default='SSD'),
        identity_name=dict(type='str', required=False),
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
    pool = module.params['pool']
    node = module.params['node']
    size = module.params['size']
    mode = module.params['mode']
    password = module.params['password']
    disk_type = module.params['disk_type']
    identity_name = module.params.get('identity_name', j.core.identity.me.instance_name)
    zos = j.sals.zos.get(identity_name)

    try:
        workload = zos.zdb.create(node, size, mode, password, pool, disk_type)
        wid = zos.workloads.deploy(workload)
        result['message'] = zos.workloads.get(wid).to_dict()
        result['changed'] = True
    except Exception as e:
        result['message'] = str(e)
        module.fail_json(msg='Failed to create subdomain', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()


if __name__ == '__main__':
    main()

