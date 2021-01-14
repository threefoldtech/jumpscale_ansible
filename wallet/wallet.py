#!/usr/bin/python


from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: Wallet

short_description: Wallet module

version_added: "0.0.1"

description: module to create and list stellar Wallets.

options:
    name:
        description: wallet name
        required: False
        type: str
    state:
        description:
            - get: get an instance (will create if it does not exist)
            - new: get a new instance and make it available as an attribute
            - delete: delete an instance (with its attribute)
            - list_all: get all instance names (stored or not)
        required: True
        choices: [ "list_all", "get", "new", "delete" ]
    secret:
        description: wallet secret
        required: False
        type: str

requirements:
  - "python >= 2.6"
  - "js-sdk"

author:
    - @dmahmouali
'''

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j


def _wallet_info(wallet):
    balances = wallet.get_balance()
    balances_data = []
    for item in balances.balances:
        balances_data.append(
            {"balance": item.balance, "asset_code": item.asset_code, "asset_issuer": item.asset_issuer}
        )

    return {
        "address": wallet.address,
        "network": wallet.network.value,
        "secret": wallet.secret,
        "balances": balances_data,
    }

def run_module():
    module_args = dict(
        name=dict(type='str', required=False),
        state=dict(type='str', required=True),
        secret=dict(type='str', required=False),
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

    try:
        name = module.params["name"]
        secret = module.params["secret"]

        if module.params["state"] == "list_all":
            wallets_names = j.clients.stellar.list_all()
            result["message"] = wallets_names
        elif module.params["state"] == "get":
            wallet = j.clients.stellar.get(name)
            result["message"] = wallet.to_dict()
        elif module.params["state"] == "delete":
                j.clients.stellar.delete(name)
                result["message"] = "deleted"
            
        elif module.params["state"] == "new":
            if j.clients.stellar.find(name):
                raise j.exceptions.Value(f"Wallet {name} already exists")
            if secret:
                result["new"] = True
                wallet = j.clients.stellar.new(name, secret)
            else:
                result["new"] = False
                wallet = j.clients.stellar.new(name)
            result["message"] = wallet.to_dict()
    except Exception as e:
            result["message"] = str(e)
    

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()

