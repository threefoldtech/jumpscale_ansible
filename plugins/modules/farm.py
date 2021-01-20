#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j



DOCUMENTATION = r'''
---
module: scheduler

short_description: farm module for zos

version_added: "1.0.0"

description: module to fetch farm info.

options:
    identity_name:
        description: identity name to be used to search. defaults to j.core.identity.me
        required: False
        type: str
    farm_id:
        description: id of the farm to search int
        required: False
        type: int
    farm_name:
        description: name of the farm to search int
        required: False
        type: str
    fact_name:
        description: used as a key to ansible fact containing the result farm
        required: False
        type: str
        default: selected_nodes


author:
    - Maged Motawea (@m-motawea)
    
'''



RETURN = r'''
ansible_facts:
    description: contains the farm info.
    type: dict
    returned: always
    sample: "{
        "email": "delandtj@incubaid.com",
        "id": 1,
        "ipaddresses": [
            {
                "address": "185.69.167.187/24",
                "gateway": "185.69.167.1",
                "reservation_id": 0
            },
            {
                "address": "185.69.167.188/24",
                "gateway": "185.69.167.1",
                "reservation_id": 0
            },
            {
                "address": "185.69.167.189/24",
                "gateway": "185.69.167.1",
                "reservation_id": 0
            }
        ],
        "iyo_organization": "",
        "location": {
            "city": "",
            "continent": "",
            "country": "",
            "latitude": 0.0,
            "longitude": 0.0
        },
        "name": "freefarm",
        "prefix_zero": "",
        "resource_prices": [],
        "threebot_id": 1,
        "wallet_addresses": [
            {
                "address": "GDUKYVYPEENRASFPVLBDA7WUTSY3ZFWWOLNOHRJBWCWYPF5PH5IHSXLX",
                "asset": "TFT"
            }
        ]
    }
}"
'''


def run_module():
    module_args = dict(
        identity_name=dict(type='str', required=False),
        farm_id=dict(type='int', required=False, default=None),
        farm_name=dict(type='str', required=False, default=None),
        fact_name=dict(type='str', required=False, default="farm"),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
    )

    identity = j.core.identity.find(module.params['identity_name']) if module.params['identity_name'] else j.core.identity.me
    explorer = identity.explorer
    try:
        farm = explorer.farms.get(farm_id=module.params["farm_id"], farm_name=module.params["farm_name"])
    except j.exceptions.NotFound:
        module.fail_json(msg=f"farm id: {module.params['farm_id']}, name: {module.params['farm_name']} does not exist")
    result["ansible_facts"] = {module.params["fact_name"]: farm.to_dict()}

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
