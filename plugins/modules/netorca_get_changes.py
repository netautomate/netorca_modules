#!/usr/bin/env python3
'''
This Ansible module gets all the change instances with the given state
for the team credentials supplied.

This module should be used for imperative approaches to deploying configuration.

TODO:
    - support filtering on service as well.

Copyright: (c) 2022, NetAutomate <info@netautomate.org>
'''

from __future__ import (absolute_import, division, print_function)

import logging

from validators import url as url_valid
from ansible.module_utils.basic import AnsibleModule # pylint: disable=import-error
try:
    # Try to import the module from the local folder
    from module_utils.netorca_base import login, get_change_instances
    from module_utils.netorca_constants import FIELDS_API_KEY, \
         FIELDS_PASS, FIELDS_USER, FIELDS_URL, FIELDS_STATE, \
            NETORCA_VALID_STATES, NETORCA_STATES_APPROVED
except ModuleNotFoundError:
    # If that failed, we are probably running inside a playbook
    # so the ansible namespace needs to be used.
    from ansible_collections.netorca.netorca_tools.plugins.module_utils.netorca_base import login, get_change_instances
    from ansible_collections.netorca.netorca_tools.plugins.module_utils.netorca_constants import NETORCA_STATES_APPROVED,  \
         FIELDS_PASS, FIELDS_USER, FIELDS_URL, FIELDS_STATE, FIELDS_UUID, \
             FIELDS_DEPLOYED_ITEM, NETORCA_VALID_STATES, FIELDS_API_KEY


__metaclass__ = type

logging.basicConfig(filename='netroca_update_change.log',level=logging.DEBUG)

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
        description : One of 'PENDING', 'ACCEPTED', 'COMPLETED'
        required: false
        type: str

    
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Ryan Checuti 
'''

EXAMPLES = r'''
# Supply API Key and get all changes
- name: Get all change instances
  netorca_get_changes:
    url: https://dev.netorca.io
    api_key: <api key here>

# Supply credentials and get only PENDING
- name: Get all change instances
  netorca_get_changes:
    url: https://dev.netorca.io
    username: team_member_a
    password: super_secure_password_here
    state: PENDING

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
change_instances:
    description: An array of the change instances returned by NetOrca
    type: array
    returned: always
message:
    description: A general message, useful when errors are encountered
    type: str
    returned: always
    sample: 'Returned 10 change instances'
'''


RESULT_FIELD_CHANGES = 'change_instances'
RESULT_FIELD_MESSAGE = 'message'
RESULT_FIELD_CHANGED = 'changed'

FIELDS = {
        FIELDS_URL: dict(type='str', required=True),
        FIELDS_API_KEY: dict(type='str', required=False, no_log=True),
        FIELDS_USER: dict(type='str', required=False),
        FIELDS_PASS: dict(type='str', required=False, no_log=True),
        FIELDS_STATE: dict(type='str', required=False)
}

def fail_module(module, msg):
    result = {
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
                f"{params[FIELDS_STATE]} is not one of {NETORCA_VALID_STATES}"
            )
    return valid

def run_module(module):
    # define available arguments/parameters a user can pass to the module

    # seed the result dict in the object
    result = {
        RESULT_FIELD_CHANGES : [],
        RESULT_FIELD_CHANGED: False,
        RESULT_FIELD_MESSAGE: 'Starting Module'
    }

    logging.debug(module.params)

    # Validate input
    if validate_params(module):

        # Login
        if FIELDS_API_KEY not in module.params or not module.params[FIELDS_API_KEY]:
            logging.debug('No API key provided, logging in')
            api_key = login(
                module.params[FIELDS_URL],
                module.params[FIELDS_USER],
                module.params[FIELDS_PASS]
            )
        else:
            logging.debug('API key provided, skipping logging in')
            api_key = module.params[FIELDS_API_KEY]

        state = NETORCA_STATES_APPROVED
        # Get instances
        if FIELDS_STATE in module.params.keys() and module.params[FIELDS_STATE]:
            state = module.params[FIELDS_STATE]

        result[RESULT_FIELD_CHANGES] = get_change_instances(
            base_url=module.params[FIELDS_URL],
            token=api_key,
            state=state
            )


        result[RESULT_FIELD_MESSAGE]= f"Found {len(result[RESULT_FIELD_CHANGES])} change items"

        logging.debug(result)
        module.exit_json(**result)

def main():
    module = AnsibleModule(
        argument_spec=FIELDS,
        supports_check_mode=True
    )
    run_module(module)


if __name__ == '__main__':
    main()
