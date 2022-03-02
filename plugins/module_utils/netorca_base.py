#!/usr/bin/env python3
'''
This module contains the methods to connect to NetOrca platform
and carry out basic functions usual for ansible integrations.



Copyright (c) 2022 NetAutomate All Rights Reserved
Date : 05/01/2022
Version : 0.1

'''
import logging
from urllib.parse import urljoin
import requests

try:
    # Try to import the module from the local folder
    import module_utils.netorca_constants as const
except  ModuleNotFoundError:
    # If that failed, we are probably running inside a playbook
    # so the ansible namespace needs to be used.
    import ansible_collections.netorca.netorca_tools.plugins.module_utils.netorca_constants  as const

_PATH_LOGIN = "/api-token-auth/"
_PATH_CHANGE_INSTANCES = "/orcabase/change_instances/"
_PATH_SERVICE_ITEMS = "/orcabase/service_items/"

def login(base_url,username,password):
    '''
    Login in to Netroca with given credentials and return a token as a string
    '''
    url = urljoin(base_url, _PATH_LOGIN)
    data = {
        "username": username,
        "password": password
         }
    logging.debug(data)
    response = requests.post(url, json=data)
    logging.debug(response.content)
    return response.json()['token']

def filter_change_instances(changes, service=''):
    ''' Filter a list of change instances based on the service '''
    result = []
    for change in changes:
        if change['service_item']['service']['name'] == service:
            result.append(change)
    return result

# Get Change Instance & Filter
def get_change_instances(base_url, token, state='', service_name='' ):
    '''
    Get all the change instances for the given team token.
    If state is not empty, filter for only the given state.
    If service is not empty, filter replies for only that service.
    '''
    url = urljoin(base_url, _PATH_CHANGE_INSTANCES)
    if state :
        url = urljoin(url, f'?state={state}')

    response = requests.get(url, headers={'Authorization': f'Token {token}'}).json()
    # FIXME handle 401, 500 or other errors
    # TODO Add filter to get only CREATE or MODIFY flags
    if response['count'] == 0:
        return []
    if service_name:
        return filter_change_instances(response['results'], service=service_name)
    return response['results']

# Get all service items for team
def get_service_items(base_url, token, service_name):
    '''
    Get all the service items that match the service_name
    '''
    url = urljoin(base_url, _PATH_SERVICE_ITEMS)
    url = urljoin(url, f'?service_name={service_name}')

    response = requests.get(url, headers={'Authorization': f'Token {token}'}).json()
    # TODO skip any 'PENDING' items
    # FIXME handle 401, 500 or other errors
    if response['count'] == 0:
        return []
    return response['results']

# Update Change Instance
def update_change_instance(base_url, token, uuid, data):
    '''
    Updates the change instance specified by the UUID
    Data should be a dictionary
    '''
    url = urljoin(base_url, _PATH_CHANGE_INSTANCES)
    url = urljoin(url, f'{uuid}/', )
    logging.debug(data)
    response = requests.put(
        url,
        headers={'Authorization': f'Token {token}'},
        json=data
        ).json()
    logging.debug(response)
    return response

# Complete all pending change_instances

def complete_change_instances(base_url, token, service_name, deployed_item=None):
    '''
    Complete all the change instances that are approved for the given
    service_name.
    '''
    result = {
        'count': 0,
        'msg': 'Starting',
        'successful': False
    }
    # Get all change instances for given service_name
    approved_changes = get_change_instances(
        base_url,
        token,
        state=const.NETORCA_STATES_APPROVED,
        service_name=service_name
    )
    # Complete the change
    for change in approved_changes:
        # Change state to Completed
        data = {
                'state': const.NETORCA_STATES_COMPLETED,
                'deployed_item': deployed_item
            }
        logging.debug("Completing CI %s",change['uuid'])
        update_change_instance(
            base_url,
            token,
            change['uuid'],
            data    
        )
        result['count'] += 1
    # TODO return success or not?
    result['successful'] = True
    result['msg'] = f"Completed {result['count']} changes"
    return result
