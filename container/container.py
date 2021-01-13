#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j

DOCUMENTATION = r'''
---
module: container

short_description: container module for zos

version_added: "1.0.0"

description: module to create containers for TF Grid.

options:
    identity_name:
        description: identity name to be used to create/extend the pool defaults to j.core.identity.me
        required: False
        type: str
    pool_id:
        description: capacity pool id to deploy the container in
        required: True
        type: int
    network_name:
        description: name of the network to attach the container to
        required: True
        type: str
    flist:
        description: url of the flist to use for the container
        required: True
        type: str
    node_id:
        description: id of the node to deploy the container on
        required: True
        type: str
    ip_address:
        description: private ip address from the chosen network to be assigned to the container
        required: True
        type: str
    env:
        description: environment vars to be passed to the container (stored in the explorer as raw text)
        required: False
        type: dict
        default: {}
    cpu:
        description: number of cpus to assign to the container
        required: False
        type: int
        default: 1
    memory:
        description: size of the memory to assign to the container
        required: False
        type: int
        default: 1024
    disk:
        description: size of the root filesystem to assign to the container
        required: False
        type: int
        default: 256
    entrypoint:
        description: entrypoint of the container
        required: False
        type: str
        default: ""
    interactive:
        description: whether to start the container as interactive (run corex) or not
        required: False
        type: bool
        default: False
    secret_env:
        description: environment vars to be passed to the container (encrypted before request)
        required: False
        type: dict
        default: {}
    public_ipv6:
        description: whether to assign a public ipv6 to the container or not
        required: False
        type: bool
        default: False
    storage_url:
        description: storage url
        required: False
        type: str
        default: "zdb://hub.grid.tf:9900"
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
    log_channel_type:
        description: type of the log channel to be used for the container
        required: False
        type: str
    log_channel_host:
        description: host ip to send container logs to
        required: False
        type: str
    log_channel_port:
        description: host port to send container logs to
        required: False
        type: str
    log_channel_name:
        description: name of the log channel to be used for the container
        required: False
        type: str
    wait:
        description: wait for workload to be successful before exit. defaults to True
        required: False
        type: bool
        default: True
    

author:
    - @m-motawea
'''

def run_module():
    module_args = dict(
        identity_name=dict(type='str', required=False),
        # required args
        pool_id=dict(type='int', required=True),
        network_name=dict(type='str', required=True),
        flist=dict(type='str', required=True),
        node_id=dict(type='str', required=True),
        ip_address=dict(type='str', required=True),
        # args with default vals
        env=dict(type='dict', required=False, default={}),
        cpu=dict(type='int', required=False, default=1),
        memory=dict(type='int', required=False, default=1024),
        disk_size=dict(type='int', required=False, default=256),
        entrypoint=dict(type='str', required=False, default=""),
        interactive=dict(type='bool', required=False, default=False),
        secret_env=dict(type='dict', required=False, default={}),
        public_ipv6=dict(type='bool', required=False, default=False),
        storage_url=dict(type='str', required=False, default="zdb://hub.grid.tf:9900"),
        volume_mounts=dict(type='dict', required=False, default={}),
        description=dict(type='str', required=False, default=""),
        metadata=dict(type='str', required=False, default=""),
        # must all be used if specified
        log_channel_type=dict(type='str', required=False),
        log_channel_host=dict(type='str', required=False),
        log_channel_port=dict(type='str', required=False),
        log_channel_name=dict(type='str', required=False),
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
    secret_env = {}
    if module.params["secret_env"]:
        for key, val in module.params["secret_env"]:
            secret_env[key] = zos.container.encrypt_secret(module.params["node_id"], val)
    cont = zos.container.create(
        node_id=module.params["node_id"],
        network_name=module.params["network_name"],
        ip_address=module.params["ip_address"],
        flist=module.params["flist"],
        capacity_pool_id=module.params["pool_id"],
        env=module.params["env"],
        cpu=module.params["cpu"],
        memory=module.params["memory"],
        disk_size=module.params["disk_size"],
        entrypoint=module.params["entrypoint"],
        interactive=module.params["interactive"],
        secret_env=secret_env,
        public_ipv6=module.params["public_ipv6"],
        storage_url=module.params["storage_url"],
    )

    if all([module.params["log_channel_type"], module.params["log_channel_host"], module.params["log_channel_port"], module.params["log_channel_name"]]):
        zos.container.add_logs(
            container=cont,
            channel_type=module.params["log_channel_type"],
            channel_host=module.params["log_channel_host"],
            channel_port=module.params["log_channel_port"],
            channel_name=module.params["log_channel_name"],
            
        )
    if module.params["volume_mounts"]:
        for mount_point, vol_id in module.params["volume_mounts"].items():
            zos.volume.attach_existing(cont, f"{vol_id}-1", mount_point)
    
    cont.info.metadata = module.params["metadata"]
    cont.info.description = module.params["description"]
    wid = zos.workloads.deploy(cont)
    
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
