#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: Identity

short_description: Identity module is responsible for managing tfexplorer user identities

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: Identity module is responsible for managing tfexplorer user identities

options:
    state:
        description: state of the specified identity
        required: true
        type: str
        choices: present, absent, list
    instance_name:
        description: name of the identity instance
        required: false
        type: str
    set_default:
        description: sets the default identity
        required: false
        type: bool
    tname:
        description: threebot name of the identity
        required: false
        type: str
    email:
        description: email of the identity
        required: false
        type: str
    words:
        description: secret words of the identity
        required: false
        type: str
    explorer:
        description: explorer name of the identity
        required: false
        type: str
        choices: mainnet, testnet, devnet
        default: testnet

# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Ahmed Samir (@AhmedSa-mir)
'''

EXAMPLES = r'''
# get identity (create if not exists)
- name: "Test get identity"
    identity:
    instance_name: ansident
    state: present
    tname: ansident.3bot
    email: ansident@incubaid.com
    words: nuclear file soda sting load frame field hold virus metal tragic grain owner skirt journey onion spirit until immune theory lunar fever scrub pelica
    explorer: devnet

# set default identity
- name: "Test set default identity"
    identity:
    instance_name: ansident
    state: present
    set_default: yes

# list identities
- name: "Test list identities"
    identity:
    state: list

# delete identity
- name: "Test delete identity"
    identity:
    instance_name: ansident
    state: absent
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

EXPLORER_URLS = {
    "mainnet": "https://explorer.grid.tf/api/v1",
    "testnet": "https://explorer.testnet.grid.tf/api/v1",
    "devnet": "https://explorer.devnet.grid.tf/api/v1",
}

def get(instance_name, tname, email, words, explorer):
    explorer_url = EXPLORER_URLS[explorer]
    return j.core.identity.get(instance_name, tname, email, words, explorer_url).to_dict()

def delete(instance_name):
    j.core.identity.delete(instance_name)

def set_default(instance_name):
    j.core.identity.set_default(instance_name)

def list_all():
    return list(j.core.identity.list_all())

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type='str', required=True, choices=['present', 'absent', 'list']),
        instance_name=dict(type='str', required=False),
        set_default=dict(type='bool', required=False, default=False),
        tname=dict(type='str', required=False),
        email=dict(type='str', required=False),
        words=dict(type='str', required=False),
        explorer=dict(type='str', required=False, choices=['mainnet', 'testnet', 'devnet'], default="testnet"),
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
        required_together=[
            ('tname', 'email', 'words')
        ],
        required_if=[
            ('state', 'present', ('tname', 'set_default'), True),
            ('state', 'absent', ('instance_name',)),
        ],
        supports_check_mode=True
    )
    
    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # main functionality of the module
    if module.params['state'] == 'absent':
        try:
            delete(module.params['instance_name'])
            result['message'] = 'OK'
        except Exception as e:
            result['message'] = str(e)
            module.fail_json(msg='Failed to delete identity', **result)
    elif module.params['state'] == 'list':
        try:
            result['message'] = list_all()
        except Exception as e:
            result['message'] = str(e)
            module.fail_json(msg='Failed to list identities', **result)
    else: # present
        if module.params['set_default']:
            try:
                set_default(module.params['instance_name'])
                result['message'] = 'OK'
            except Exception as e:
                result['message'] = str(e)
                module.fail_json(msg='Failed to set default identity', **result)
        else:
            try:
                result['message'] = get(instance_name= module.params['instance_name'],
                    tname=module.params['tname'],
                    email=module.params['email'],
                    words=module.params['words'],
                    explorer=module.params['explorer'])
            except Exception as e:
                result['message'] = str(e)
                module.fail_json(msg='Failed to get identity', **result)

    result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()


if __name__ == '__main__':
    main()

