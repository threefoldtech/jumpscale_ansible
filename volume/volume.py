#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j



DOCUMENTATION = r'''
---
module: volume

short_description: volume module for zos

version_added: "1.0.0"

description: module to create volumes for TF Grid.

options:
    identity_name:
        description: identity name to be used to deploy the container defaults to j.core.identity.me
        required: False
        type: str
    pool_id:
        description: capacity pool id to deploy the volume in
        required: True
        type: int
    node_id:
        description: id of the node to deploy the volume on
        required: True
        type: str
    size:
        description: size of the volume in GB
        required: True
        type: int
    type:
        description: disk type for the volume
        required: False
        type: str
        choices: ssd, hdd
        default: ssd
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
        identity_name=dict(type='str', required=False),
        pool_id=dict(type='int', required=True),
        node_id=dict(type='str', required=True),
        size=dict(type='int', required=True),
        type=dict(type='str', required=False, default='ssd', choices=['ssd', 'hdd']),
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
        supports_check_mode=True
    )

    zos = j.sals.zos.get(module.params['identity_name'])
    vol = zos.volume.create(
        node_id=module.params['node_id'],
        pool_id=module.params['pool_id'],
        size=module.params['size'],
        type=module.params['type'].upper()
    )
    vol.info.description = module.params['description']
    vol.info.description = module.params['metadata']
    wid = zos.workloads.deploy(vol)

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
