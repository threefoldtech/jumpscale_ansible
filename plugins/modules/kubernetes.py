#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j



DOCUMENTATION = r'''
---
module: kubernetes

short_description: kubernetes module for zos

version_added: "1.0.0"

description: module to create kubernetes for TF Grid.

options:
    identity_name:
        description: identity name to be used to deploy the kubernetes VM defaults to j.core.identity.me
        required: False
        type: str
    pool_id:
        description: capacity pool id to deploy the kubernetes VM in
        required: True
        type: int
    network_name:
        description: name of the network to attach the kubernetes VM to
        required: True
        type: str
    node_id:
        description: id of the node to deploy the kubernetes VM on
        required: True
        type: str
    ip_address:
        description: private ip address from the chosen network to be assigned to the kubernetes VM
        required: True
        type: str
    cluster_secret:
        description: k8s cluster secret passed to zos
        required: True
        type: str
    size:
        description: k8s vm size as defined in zos
        required: False
        type: int
        default: 1
    ssh_keys:
        description: path of public key files to be added to the VM
        required: False
        type: list
        default: []
    public_ip_wid:
        description: workload id of the public ip to attach to the vm
        required: False
        type: int
        default: 0
    master_ip:
        description: ip address of the master VM. if specified the VM will be deployed as worker
        required: False
        type: str
        default: None
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
        network_name=dict(type='str', required=True),
        cluster_secret=dict(type='str', required=True),
        ip_address=dict(type='str', required=True),
        size=dict(type='int', required=False, default=1),
        ssh_keys=dict(type='list', required=False, default=[]),
        public_ip_wid=dict(type='int', required=False, default=0),
        master_ip=dict(type='str', required=False, default=None),
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

    ssh_keys = []

    for key in module.params["ssh_keys"]:
        key_path = j.sals.fs.expanduser(key)
        key_text = j.sals.fs.read_file(key_path)
        ssh_keys.append(key_text.strip())

    zos = j.sals.zos.get(module.params['identity_name'])
    if not module.params["master_ip"]:
        # deploy master
        k8s = zos.kubernetes.add_master(
            node_id=module.params["node_id"],
            network_name=module.params["network_name"],
            cluster_secret=module.params["cluster_secret"],
            ip_address=module.params["ip_address"],
            size=module.params["size"],
            ssh_keys=ssh_keys,
            pool_id=module.params["pool_id"],
            public_ip_wid=module.params["public_ip_wid"],
        )
    else:
        # deploy worker
        k8s = zos.kubernetes.add_worker(
            node_id=module.params["node_id"],
            network_name=module.params["network_name"],
            cluster_secret=module.params["cluster_secret"],
            ip_address=module.params["ip_address"],
            size=module.params["size"],
            master_ip=module.params["master_ip"],
            ssh_keys=ssh_keys,
            pool_id=module.params["pool_id"],
            public_ip_wid=module.params["public_ip_wid"],
        )
    k8s.info.description = module.params['description']
    k8s.info.description = module.params['metadata']

    wid = zos.workloads.deploy(k8s)

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

