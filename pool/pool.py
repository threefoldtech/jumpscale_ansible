#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j
import gevent


DOCUMENTATION = r'''
---
module: Pool

short_description: Pool module

version_added: "1.0.0"

description: module to create and extend pools for the TF Grid.

options:
    identity_name:
        description: identity name to be used to create/extend the pool defaults to j.core.identity.me
        required: False
        type: str
    wallet_name:
        description: wallet name to be used in pool payment
        required: True
        type: str
    farm_name:
        description: name of the farm to create the pool on. required in case of new pools (no pool_id sepecified)
        required: False
        type: str
    cus:
        description: how much cus (compute units) to use in pool creation/extension
        required: False
        type: int
        default: 0
    sus:
        description: how much sus (storage units) to use in pool creation/extension
        required: False
        type: int
        default: 0
    ipv4us:
        description: how much ipv4us (public ip units) to use in pool creation/extension
        required: False
        type: int
        default: 0
    pool_id:
        description: id of the pool to extend.
        required: False
        type: int
    wait:
        description: wait for payment to be successful before exit. defaults to True
        required: False
        type: bool
        default: True


author:
    - Maged Motawea (@m-motawea)
'''


RETURN = r'''
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
message:
    description: The output message that the test module generates.
    type: dict
    returned: always
    sample: "{'reservation_id': 3391, 'escrow_information': {'address': 'GCB5JCO44PB7GWXH6MWJMP6DNZKDSYQCSIWDFRP7O3R6B32CL4JNKZXK', 'asset': 'TFT:GBOVQKJYHXRR3DX6NOX2RRYFRCUMSADGDESTDNBDS6CDVLGVESRTAC47', 'amount': 0}}"
'''


def run_module():
    module_args = dict(
        identity_name=dict(type='str', required=False),
        wallet_name=dict(type='str', required=True),
        farm_name=dict(type='str', required=False),
        cus=dict(type='int', required=False, default=0),
        sus=dict(type='int', required=False, default=0),
        ipv4us=dict(type='int', required=False, default=0),
        pool_id=dict(type='int', required=False, default=0),  # if sepecified it will extend
        wait=dict(type='bool', required=False, default=True),
        node_ids=dict(type='list', required=False),
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
    wallet = j.clients.stellar.find(module.params["wallet_name"])
    
    if module.params["pool_id"]:
        pool_info = zos.pools.extend(
            pool_id=module.params["pool_id"],
            cu=module.params["cus"],
            su=module.params["sus"],
            ipv4us=module.params["ipv4us"],
            node_ids=module.params["node_ids"],
        )
    else:
        pool_info = zos.pools.create(
            cu=module.params["cus"],
            su=module.params["sus"],
            ipv4us=module.params["ipv4us"],
            farm=module.params["farm_name"]
        )
    
    zos.billing.payout_farmers(wallet, pool_info)
    
    result["message"] = pool_info.to_dict()
    result["changed"] = True
    if module.params["wait"] and any([module.params["cus"], module.params["sus"], module.params["ipv4us"]]):
        payment = zos.pools.get_payment_info(pool_info.reservation_id)
        while payment.expiration.timestamp() > j.data.time.utcnow().timestamp:
            if payment.paid and any([payment.released, payment.canceled]):
                break
            gevent.sleep(2)
            payment = zos.pools.get_payment_info(pool_info.reservation_id)
        if not all([payment.paid, payment.released]):
            result["changed"] = False
            result["error"] = payment.cause

    
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()

