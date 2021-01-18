#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: Metadata

short_description: Metadata module is responsible for managing workloads metadata e.g. encryption, decryption, etc...

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Metadata module is responsible for managing workloads metadata e.g. encryption, decryption, etc...


options:
    state:
        description: state of the specified proxy
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

# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

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
# These are examples of possible return values, and in general should use other names for return values.
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
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type='str', required=True, choices=['encrypt', 'decrypt']),
        metadata=dict(type='dict', required=False),
        encrypted_metadata=dict(type='str', required=False),
        identity_name=dict(type='str', required=False),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        mutually_exclusive=[('metadata', 'encrypted_metadata',),],
        required_one_of=[('metadata', 'encrypted_metadata',),],
        required_if=[
            ('state', 'encrypt', ('metadata',),),
            ('state', 'decrypt', ('encrypted_metadata',),)
        ],
        supports_check_mode=True
    )
    
    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # main functionality of the module
    identity_name = module.params.get('identity_name', j.core.identity.me.instance_name)
    if module.params['state'] == 'encrypt':
        try:
            metadata = j.data.serializers.json.dumps(module.params['metadata'])
            pk = j.core.identity.get(identity_name).nacl.signing_key.verify_key.to_curve25519_public_key()
            sk = j.core.identity.get(identity_name).nacl.signing_key.to_curve25519_private_key()
            box = Box(sk, pk)
            encrypted_metadata = base64.b85encode(box.encrypt(metadata.encode())).decode()
            result['message'] = encrypted_metadata
            result['changed'] = True
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
            result['changed'] = True
        except Exception as e:
            result['message'] = str(e)
            module.fail_json(msg='Failed to decrypt metadata', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()


if __name__ == '__main__':
    main()

