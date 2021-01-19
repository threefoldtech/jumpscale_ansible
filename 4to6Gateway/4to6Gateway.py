#!/usr/bin/python


DOCUMENTATION = r'''
---
module: 4to6Gateway

short_description: 4to6Gateway module is responsible for creating 4to6Gateway on tf farms gateways


version_added: "1.0.0"

description: 4to6Gateway module is responsible for creating 4to6Gateways on tf farms gateways
             currently creating 4to6Gateway is only supported

options:
    pool:
        description: id of the pool to choose gateway on
        required: true
        type: int
    gateway:
        description: id of the node of the gateway to create 4to6Gateway on
        required: true
        type: str
    public_key:
        description: wireguard public key
        required: true
        type: str
    identity_name:
        description: identity instance name (if not provided will use the default identity)
        required: false
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
    - Mahmoud Ayoub (@dmahmouali)
'''

EXAMPLES = r'''
---
- name: Test js-sdk 4to6Gateway module
  hosts: localhost
  tasks:
    - name: "Test create 4to6Gateway"
      subdomain:
        state: present
        pool: 20
        gateway: EwPS7nPZHd5KH6YH7PtbmUpJUyWgseqsqS7cGhjXLUjz
        identity_name: ayoubmain
        description: "test 4to6Gateway"
        metadata: "test: test"
      register: result

    - debug:
        msg: "{{ result['message']}}"
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
wgconf:
    description: path to the generate wireguard configuration file.
    type: str
'''
from textwrap import dedent

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j

def run_module():
    module_args = dict(
        pool=dict(type='int', required=True),
        gateway=dict(type='str', required=True),
        public_key=dict(type='str', required=True),
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
        supports_check_mode=True
    )
    
    if module.check_mode:
        module.exit_json(**result)

    if module.params['identity_name']:
        identity_name = module.params['identity_name']
    else:
        identity_name = j.core.identity.me.instance_name
    zos = j.sals.zos.get(identity_name)

    gateway_id = module.params['gateway']
    pool_id = module.params['pool']
    public_key = module.params['public_key']
    description = module.params['description']
    metadata = module.params['metadata']
    privatekey = "enter private key here"

    workload = zos.gateway.gateway_4to6(gateway_id, public_key ,pool_id)
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

    reservation_result = zos.workloads.get(wid).info.result
    cfg = j.data.serializers.json.loads(reservation_result.data_json)
    wgconfigtemplate = """\
    [Interface]
    Address = {{cfg.ips[0]}}
    PrivateKey = {{privatekey}}
    {% for peer in cfg.peers %}
    [Peer]
    PublicKey = {{peer.public_key}}
    AllowedIPs = {{",".join(peer.allowed_ips)}}
    {% if peer.endpoint -%}
    Endpoint = {{peer.endpoint}}
    {% endif %}
    {% endfor %}
        """
    wgconfig_path = f"./{wid}.conf"
    wgconfig_data = j.tools.jinja2.render_template(
        template_text=dedent(wgconfigtemplate), cfg=cfg, privatekey=privatekey
    )
    j.sals.fs.touch(wgconfig_path)
    j.sals.fs.write_file(wgconfig_path, wgconfig_data)
    result["wgconf"] = wgconfig_path


    module.exit_json(**result)

def main():
    run_module()


if __name__ == '__main__':
    main()

