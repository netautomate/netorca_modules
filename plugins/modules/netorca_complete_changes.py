#!/usr/bin/env python3
'''
This Ansible module searches the NetOrca platform for change instances that
are of a particular services and that are in 'ACCEPTED' state. Any change
instances found are marked as completed.

Copyright: (c) 2022, NetAutomate <info@netautomate.org>
'''
from __future__ import (absolute_import, division, print_function)

import logging
from typing_extensions import Required
from validators import url as url_valid
from ansible.module_utils.basic import AnsibleModule # pylint: disable=import-error
try:
    # Try to import the module from the local folder
    from module_utils.netorca_base import login, complete_change_instances
    from module_utils.netorca_constants import FIELDS_SERVICE, FIELDS_API_KEY, \
     FIELDS_PASS, FIELDS_USER, FIELDS_URL, FIELDS_DEPLOYED_ITEM
except ModuleNotFoundError:
    # If that failed, we are probably running inside a playbook
    # so the ansible namespace needs to be used.
    from ansible_collections.netorca.netorca_tools.plugins.module_utils.netorca_base import login, update_change_instance
    from ansible_collections.netorca.netorca_tools.plugins.module_utils.netorca_constants import NETORCA_STATES_APPROVED,  \
         FIELDS_PASS, FIELDS_USER, FIELDS_URL, FIELDS_STATE, FIELDS_UUID, \
             FIELDS_DEPLOYED_ITEM, NETORCA_VALID_STATES, FIELDS_API_KEY


logging.basicConfig(filename='netorca_update_change.log',level=logging.DEBUG)

__metaclass__ = type

DOCUMENTATION = r'''
---
module: netorca_complete_changes

short_description: Complete all the APPROVED changes

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "0.1.0"

description: This modules sets all the APPROVED change instances to COMPLETED 
            for a particular service_name

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
    service_name:
        description : The name of the service for which all change instances \
            should be marked as complete
        required: true
        type: str

    
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Ryan Checuti 
'''

EXAMPLES = r'''
- name: Set change to completed
  netorca_complete_changes:
    url: https://dev.netorca.io
    api_key: <api key here>
    service_name: <name of service>

- name: Update change and add deployed_item
  netorca_update_change
    url: https://dev.netorca.io
    username: team_member_a
    password: super_secure_password_here
    service_name: <name of service>

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
        FIELDS_SERVICE: dict(type='str', required=True),
        FIELDS_DEPLOYED_ITEM: dict(tyep='dict', required=True)
}

def fail_module(module, msg):
    result = {
        'message': msg,
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

    if not FIELDS_SERVICE in keys or not params[FIELDS_SERVICE]:
        valid = False
        fail_module(module, f"Missing {FIELDS_SERVICE}")
    return valid


def run_module(module):
    # define available arguments/parameters a user can pass to the module

    # seed the result dict in the object
    result = dict(
        changed=False,
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

        reply = complete_change_instances(
                base_url=module.params[FIELDS_URL],
                token=api_key,
                service_name= module.params[FIELDS_SERVICE],
                deployed_item= module.params[FIELDS_DEPLOYED_ITEM] 
        )
        if not reply['successful']:
            fail_module(module, reply['msg'])
        if reply['count'] > 0:
            result['changed']= True
        result['message']= reply['msg']

        module.exit_json(**result)

def main():
    module = AnsibleModule(
        argument_spec=FIELDS,
        supports_check_mode=True
    )
    run_module(module)

if __name__ == '__main__':
    main()
