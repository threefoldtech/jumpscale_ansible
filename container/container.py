#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j



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
