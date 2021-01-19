#!/usr/bin/python



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
  - "python"
  - "js-grid"

author:
    - Mahmoud Ayoub (@dmahmouali)
'''

EXAMPLES= r'''
- name: "Test get Wallet"
    wallet:
    name: "testmainnet"
    state: "get"

- name: "Test list all Wallet"
    wallet:
    state: "list_all"
    register: result

- name: "Test delete Wallet"
    wallet:
    name: "test_mahmoud"
    state: "delete"

- name: "Test create Wallet"
    wallet:
    name: "new_one"
    state: "new"

- name: "Test import Wallet"
    wallet:
    name: "new_one"
    state: "new"
    secret: "SDCDFP73LI527FZPT66LZHDWFRQZB7OVQYB7EZKDLAPVJQGJCKW7CEWM"
'''

RETURN = r'''
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'OK'
out:
    description: The output message that the test module generates.
    type: dict, list
    returned: changed
    sample: {
        "address": "GAJHJFHE5L7UQ4QJWU62TVXTUUEGJTI2UXLNAGAL4Q7BXKSENBSOMSHL",
        "balances": {
            "TFT": "0.0000000",
            "XLM": "3.5999900"
        },
        "network": "STD",
        "secret": "SAZGIH3CETPAFQ32GDYVJTHS7NQJAH6CWEZ56WFUMZBE6QVLPQTFEYFL"
    }
    sample: [
        test_mainnet,
        vdc_wallet,
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j


def _get_balance(wallet):
    balances = wallet.get_balance()
    balances_data = {}
    for item in balances.balances:
        balances_data[item.asset_code] = item.balance

    return balances_data

def run_module():
    module_args = dict(
        name=dict(type='str', required=False),
        state=dict(type='str', choices=['list_all', 'get', 'new', 'delete'], required=True),
        secret=dict(type='str', required=False),
    )

    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'get', ('name',)),
            ('state', 'new', ('name',)),
            ('state', 'delete', ('name',)),
        ],
    )

    name = module.params["name"]
    secret = module.params["secret"]

    if module.params["state"] == "list_all":
        wallets_names = j.clients.stellar.list_all()
        result["message"] = "OK"
        result["out"] = wallets_names
    

    elif module.params["state"] == "get":
        if not j.clients.stellar.find(name):
            module.fail_json(msg=f"Wallet {name} not exists", **result)
        wallet = j.clients.stellar.get(name)
        wallet_dict = wallet.to_dict()
        wallet_dict.update({"balances": _get_balance(wallet)})
        result["message"] = "OK"
        result["out"] = wallet_dict
    

    elif module.params["state"] == "delete":
        if not j.clients.stellar.find(name):
            module.fail_json(msg=f"Wallet {name} not exists", **result)
        j.clients.stellar.delete(name)
        result["message"] = "deleted"
        result["changed"] = True
        result["out"] = f"Wallet {name} deleted"
        

    elif module.params["state"] == "new":
        if j.clients.stellar.find(name):
            module.fail_json(msg=f"Wallet {name} already exists", **result)
        
        if secret:
            wallet = j.clients.stellar.new(name, secret=secret)
            wallet_dict = wallet.to_dict()
            try:
                _get_balance(wallet)
            except Exception as e:
                j.clients.stellar.delete(name=name)
                result['message'] = str(e)
                module.fail_json(msg='Error in wallet get balaces', **result)
        else:
            wallet = j.clients.stellar.new(name)
            try:
                wallet.activate_through_threefold_service()
            except Exception as e:
                j.clients.stellar.delete(name=name)
                result['message'] = str(e)
                module.fail_json(msg='Error in wallet activation', **result)

            try:
                wallet.add_known_trustline("TFT")
            except Exception as e:
                j.clients.stellar.delete(name=name)
                result['message'] = str(e)
                module.fail_json(msg=f'Failed to add trustlines to wallet {name}. Any changes made will be reverted.', **result)
            wallet_dict = wallet.to_dict()

        wallet.save()
        wallet_dict.update({"balances": _get_balance(wallet)})
        result["message"] = "OK"
        result["changed"] = True
        result["out"] = wallet_dict
    

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()