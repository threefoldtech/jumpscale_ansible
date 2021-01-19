#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j

DOCUMENTATION = r'''
---
module: ZDB

short_description: ZDB module is responsible for managing ZDBs. Currently creating ZDB is only supported.

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


author:
    - Ahmed Samir (@AhmedSa-mir)
'''

EXAMPLES = r'''
- name: "Test create ZDB"
    zdb:
        state: present
        pool: 229 
        node: 26ZATmd3K1fjeQKQsi8Dr7bm9iSRa3ePsV8ubMcbZEuY
        size: 2
        mode: "SEQ"
        password: ""
        disk_type: "SSD"
        identity_name: asamir_test
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


def run_module():
    module_args = dict(
        state=dict(type='str', required=True, choices=['present']),
        pool=dict(type='int', required=True),
        node=dict(type='str', required=True),
        size=dict(type='int', required=True),
        mode=dict(type='str', required=True, choices=['SEQ', 'USER']),
        password=dict(type='str', required=True),
        disk_type=dict(type='str', required=False, choices=['SSD', 'HDD'], default='SSD'),
        identity_name=dict(type='str', required=False),
        description=dict(type='str', required=False, default=""),
        metadata=dict(type='str', required=False, default=""),
        # wait for workload flag
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
    
   
    pool = module.params['pool']
    node = module.params['node']
    size = module.params['size']
    mode = module.params['mode']
    password = module.params['password']
    disk_type = module.params['disk_type']
    identity_name = module.params.get('identity_name', j.core.identity.me.instance_name)
    zos = j.sals.zos.get(identity_name)

    workload = zos.zdb.create(node, size, mode, password, pool, disk_type)
    workload.info.description = module.params['description']
    workload.info.description = module.params['metadata']
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

