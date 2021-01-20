#!/usr/bin/python



DOCUMENTATION = r'''
---
module: Metadata

short_description: Metadata module is responsible for managing workloads metadata e.g. encryption, decryption, etc...

version_added: "1.0.0"

description: Metadata module is responsible for managing workloads metadata e.g. encryption, decryption, etc...


options:
    state:
        description: state of the specified data
        required: true
        type: str
        choices: encrypt, decrypt
    metadata:
        description: data to encrypt
        required: false
        type: dict
    decrypted_metadata:
        description: data to decrypt 
        required: false
        type: str
    identity_name:
        description: identity instance name (if not provided will use the default identity)
        required: false
        type: str


author:
    - Ahmed Samir (@AhmedSa-mir)
'''

EXAMPLES = r'''
# encrypt decrypt metadata
- name: "Test encrypt metadata"
    metadata:
        state: encrypt
        metadata:
          test: "test"
        identity_name: asamir_test
    register: encrypted_data

- debug:
    msg: "{{ encrypted_data['message']}}"

- name: "Test decrypt metadata"
    metadata:
        state: decrypt
        encrypted_metadata: "{{ encrypted_data['message']}}"
        identity_name: asamir_test 
    register: decrypted_data

- debug:
    msg: "{{ decrypted_data['message']}}"
'''

RETURN = r'''
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'OK'
'''

from ansible.module_utils.basic import AnsibleModule
from jumpscale.loader import j

import base64
from nacl.public import Box

def run_module():
    module_args = dict(
        state=dict(type='str', required=True, choices=['encrypt', 'decrypt']),
        metadata=dict(type='dict', required=False),
        encrypted_metadata=dict(type='str', required=False),
        identity_name=dict(type='str', required=False),
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('metadata', 'encrypted_metadata',),],
        required_one_of=[('metadata', 'encrypted_metadata',),],
        required_if=[
            ('state', 'encrypt', ('metadata',),),
            ('state', 'decrypt', ('encrypted_metadata',),)
        ],
    )

    identity_name = module.params.get('identity_name', j.core.identity.me.instance_name)
    if module.params['state'] == 'encrypt':
        try:
            metadata = j.data.serializers.json.dumps(module.params['metadata'])
            pk = j.core.identity.get(identity_name).nacl.signing_key.verify_key.to_curve25519_public_key()
            sk = j.core.identity.get(identity_name).nacl.signing_key.to_curve25519_private_key()
            box = Box(sk, pk)
            encrypted_metadata = base64.b85encode(box.encrypt(metadata.encode())).decode()
            result['message'] = encrypted_metadata
        except Exception as e:
            result['message'] = str(e)
            module.fail_json(msg='Failed to encrypt metadata', **result)
    else:
        try:
            identity = j.core.identity.get(identity_name)
            pk = identity.nacl.signing_key.verify_key.to_curve25519_public_key()
            sk = identity.nacl.signing_key.to_curve25519_private_key()
            box = Box(sk, pk)
            decrypted_metadata = box.decrypt(base64.b85decode(module.params['encrypted_metadata'].encode())).decode()
            result['message'] = decrypted_metadata
        except Exception as e:
            result['message'] = str(e)
            module.fail_json(msg='Failed to decrypt metadata', **result)

    module.exit_json(**result)

def main():
    run_module()


if __name__ == '__main__':
    main()

