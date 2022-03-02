#!/usr/bin/env python3
'''
This Ansible Module will update a single change instnace on the Netorca
platform.

Copyright: (c) 2022, NetAutomate <info@netautomate.org>
'''
from __future__ import (absolute_import, division, print_function)

import logging
from validators import url as url_valid
from ansible.module_utils.basic import AnsibleModule # pylint: disable=import-error
try:
    # Try to import the module from the local folder
    from module_utils.netorca_base import login, update_change_instance
    from module_utils.netorca_constants import FIELDS_API_KEY, \
         FIELDS_PASS, FIELDS_USER, FIELDS_URL, FIELDS_STATE, FIELDS_UUID, \
             FIELDS_DEPLOYED_ITEM, NETORCA_VALID_STATES
except ModuleNotFoundError:
    # If that failed, we are probably running inside a playbook
    # so the ansible namespace needs to be used.
    from ansible_collections.netorca.netorca_tools.plugins.module_utils.netorca_base import login, update_change_instance
    from ansible_collections.netorca.netorca_tools.plugins.module_utils.netorca_constants import NETORCA_STATES_APPROVED,  \
         FIELDS_PASS, FIELDS_USER, FIELDS_URL, FIELDS_STATE, FIELDS_UUID, \
             FIELDS_DEPLOYED_ITEM, NETORCA_VALID_STATES, FIELDS_API_KEY

__metaclass__ = type

logging.basicConfig(filename='netorca_update_change.log',level=logging.DEBUG)

DOCUMENTATION = r'''
---
module: netorca_get_changes

short_description: Get Change Instances form NetOrca 

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.1.0"

description: This modules gets the change instances for a team in Netorca

options:
    url:
        description : Base URL for NetOrca. 
        required: true
        type: str
    api_key:
        description : API Key generataed for tema. If this is not specified, \
            username and password need to be provided.
        required: false
        type: str
    username:
        description : Username for account in the team. Use when no API KEY is \
            available.
        required: false
        type: str
    password:
        description : Password for account in the team. Use when no API KEY is \
            available.
        required: false
        type: str
    state:
        description : The final state that the change should be in
            available.
        required: true
        type: str
    uuid: 
        description : UUID for the change instance that should be updated
            available.
        required: true
        type: str
    deployed_item:
        description : A dictionary that contains all the deployed_item values
        required: false
        type: dict

    
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Ryan Checuti 
'''

EXAMPLES = r'''
- name: Set change to completed
  netorca_update_change:
    url: https://dev.netorca.io
    api_key: <api key here>
    state: COMPLETED
    uuid: <long uuid>

- name: Update change and add deployed_item
  netorca_update_change
    url: https://dev.netorca.io
    username: team_member_a
    password: super_secure_password_here
    state: COMPLETED
    uuid: <long uuid>

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
changed:
    description: A boolean to show whether the value was changed or not.
    type: bool
    returned: always
message:
    description: A general message, useful when errors are encountered
    type: str
    returned: always
'''


FIELDS = {
        FIELDS_URL: dict(type='str', required=True),
        FIELDS_API_KEY: dict(type='str', required=False, no_log=True),
        FIELDS_USER: dict(type='str', required=False),
        FIELDS_PASS: dict(type='str', required=False, no_log=True),
        FIELDS_STATE: dict(type='str', required=True),
        FIELDS_UUID: dict(type='str', required=True),
        FIELDS_DEPLOYED_ITEM: dict(type='dict', required=False)
}

def fail_module(module, msg):
    result = {
        'meesage': msg,
        'change_instances': []
    }
    logging.error(msg)
    module.fail_json(msg=msg, **result)

def validate_params(module):
    params = module.params
    keys = params.keys()
    valid = True
    # Check that either api_key or username + password supplied
    if not FIELDS_API_KEY in keys:
        if not ( FIELDS_USER in keys and FIELDS_PASS in keys):
            valid = False
            fail_module(
                module,
                "If no api_key specified, username and passowrd required"
            )

    # Check that URL is a valid URL
    if not url_valid(params[FIELDS_URL]):
        valid = False
        fail_module(module, f"{params[FIELDS_URL]} is not a valid url")
   # Check that State is one of valid states
    if FIELDS_STATE in keys:
        if not params[FIELDS_STATE] in NETORCA_VALID_STATES:
            valid = False
            fail_module(
                module,
                f"{params[FIELDS_STATE]} is not one of {NETORCA_VALID_STATES}")
    # TODO Add validation of deployed_item
    # TODO Add validation of UUID
    return valid


def run_module(module):
    # define available arguments/parameters a user can pass to the module

    # seed the result dict in the object
    result = dict(
        changed=False,
        change_instance = {},
        message=''
    )

    # Validate input
    if validate_params(module):

        # Login
        if FIELDS_API_KEY not in module.params or not module.params[FIELDS_API_KEY]:
            api_key = login(
                module.params[FIELDS_URL],
                module.params[FIELDS_USER],
                module.params[FIELDS_PASS]
            )
        else:
            api_key = module.params[FIELDS_API_KEY]

        data = {
            'description': {'test':'test'},
            'state': module.params[FIELDS_STATE],
        }
        if FIELDS_DEPLOYED_ITEM in module.params and module.params[FIELDS_DEPLOYED_ITEM]:
            data.update({'deployed_item': module.params[FIELDS_DEPLOYED_ITEM] })

        reply = update_change_instance(
                base_url=module.params[FIELDS_URL],
                token=api_key,
                uuid=module.params[FIELDS_UUID],
                data=data
        )
        result['change_instance']=reply
        result['changed']= True
        result['message']= f"Updated {module.params[FIELDS_UUID]} change item"

        module.exit_json(**result)

def main():
    module = AnsibleModule(
        argument_spec=FIELDS,
        supports_check_mode=True
    )
    run_module(module)

if __name__ == '__main__':
    main()
