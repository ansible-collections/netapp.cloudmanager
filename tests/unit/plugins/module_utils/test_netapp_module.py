# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2021, Laurent Nicolas <laurentn@netapp.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

""" unit tests for module_utils netapp.py

    Provides wrappers for cloudmanager REST APIs
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# import copy     # for deepcopy
import json
import sys
import pytest
try:
    HAS_REQUESTS_EXC = True
except ImportError:
    HAS_REQUESTS_EXC = False

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.cloudmanager.tests.unit.compat.mock import patch
import ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module import cmp as nm_cmp, NetAppModule
if (not netapp_utils.HAS_REQUESTS or not HAS_REQUESTS_EXC) and sys.version_info < (3, 5):
    pytestmark = pytest.mark.skip('skipping as missing required imports on 2.6 and 2.7')


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class mockResponse:
    def __init__(self, json_data, status_code, headers=None):
        self.json_data = json_data
        self.status_code = status_code
        self.content = json_data
        self.headers = headers or {}

    def json(self):
        return self.json_data


def create_module(args):
    argument_spec = netapp_utils.cloudmanager_host_argument_spec()
    set_module_args(args)
    module = basic.AnsibleModule(argument_spec)
    return module


def create_restapi_object(args):
    module = create_module(args)
    return netapp_utils.CloudManagerRestAPI(module)


def mock_args(feature_flags=None, client_id=None):
    args = {
        'refresh_token': 'ABCDEFGS'
    }
    return args


TOKEN_DICT = {
    'access_token': 'access_token',
    'token_type': 'token_type'
}


def test_cmp():
    assert nm_cmp(None, 'x') == -1
    assert nm_cmp('y', 'x') == 1
    assert nm_cmp('y', 'X') == 1
    assert nm_cmp(['x', 'y'], ['x', 'X']) == 1
    assert nm_cmp(['x', 'x'], ['x', 'X']) == 0


def test_set_parameters():
    helper = NetAppModule()
    helper.set_parameters({'a': None, 'b': 'b'})
    assert 'a' not in helper.parameters
    assert 'b' in helper.parameters


def test_cd_action():
    desired = {}
    helper = NetAppModule()
    assert helper.get_cd_action(None, desired) == 'create'
    desired['state'] = 'present'
    assert helper.get_cd_action(None, desired) == 'create'
    assert helper.get_cd_action({}, desired) is None
    desired['state'] = 'absent'
    assert helper.get_cd_action(None, desired) is None
    assert helper.get_cd_action({}, desired) == 'delete'


def test_compare_and_update_values():
    current = {'a': 'a', 'b': 'b'}
    desired = {}
    desired_key = []
    helper = NetAppModule()
    assert helper.compare_and_update_values(current, desired, desired_key) == ({}, False)
    desired_key = ['a']
    assert helper.compare_and_update_values(current, desired, desired_key) == ({'a': 'a'}, False)
    desired = {'a': 'a'}
    assert helper.compare_and_update_values(current, desired, desired_key) == ({'a': 'a'}, False)
    desired = {'a': 'c'}
    assert helper.compare_and_update_values(current, desired, desired_key) == ({'a': 'c'}, True)


@patch('requests.request')
def test_get_working_environments_info(mock_request):
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data={'a': 'b'}, status_code=200),
        mockResponse(json_data={'c': 'd'}, status_code=500)
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    assert helper.get_working_environments_info(rest_api, '') == ({'a': 'b'}, None)
    assert helper.get_working_environments_info(rest_api, '') == ({'c': 'd'}, '500')


def test_look_up_working_environment_by_name_in_list():
    we_list = [{'name': 'bob', 'b': 'b'}, {'name': 'chuck', 'c': 'c'}]
    helper = NetAppModule()
    assert helper.look_up_working_environment_by_name_in_list(we_list, 'bob') == (we_list[0], None)
    error = "look_up_working_environment_by_name_in_list: Working environment not found"
    assert helper.look_up_working_environment_by_name_in_list(we_list, 'alice') == (None, error)


@patch('requests.request')
def test_get_working_environment_details_by_name(mock_request):
    we_list = [{'name': 'bob', 'b': 'b'}, {'name': 'chuck', 'c': 'c'}]
    json_data = {'onPremWorkingEnvironments': [],
                 'gcpVsaWorkingEnvironments': [],
                 'azureVsaWorkingEnvironments': [],
                 'vsaWorkingEnvironments': []
                 }
    json_data_onprem = dict(json_data)
    json_data_onprem['onPremWorkingEnvironments'] = we_list
    json_data_gcp = dict(json_data)
    json_data_gcp['gcpVsaWorkingEnvironments'] = we_list
    json_data_azure = dict(json_data)
    json_data_azure['azureVsaWorkingEnvironments'] = we_list
    json_data_aws = dict(json_data)
    json_data_aws['vsaWorkingEnvironments'] = we_list
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),        # OAUTH
        mockResponse(json_data={'a': 'b'}, status_code=500),        # exists
        mockResponse(json_data={'a': 'b'}, status_code=200),        # exists
        mockResponse(json_data={'c': 'd'}, status_code=400),        # get all
        mockResponse(json_data={'a': 'b'}, status_code=200),        # exists
        mockResponse(json_data=json_data_onprem, status_code=200),  # get all
        mockResponse(json_data={'a': 'b'}, status_code=200),        # exists
        mockResponse(json_data=json_data_gcp, status_code=200),     # get all
        mockResponse(json_data={'a': 'b'}, status_code=200),        # exists
        mockResponse(json_data=json_data_azure, status_code=200),   # get all
        mockResponse(json_data={'a': 'b'}, status_code=200),        # exists
        mockResponse(json_data=json_data_aws, status_code=200),     # get all
        mockResponse(json_data={'a': 'b'}, status_code=200),        # exists
        mockResponse(json_data=json_data, status_code=200),         # get all
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    assert helper.get_working_environment_details_by_name(rest_api, '', 'name') == (None, '500')
    assert helper.get_working_environment_details_by_name(rest_api, '', 'name') == (None, '400')
    assert helper.get_working_environment_details_by_name(rest_api, '', 'bob') == (we_list[0], None)
    assert helper.get_working_environment_details_by_name(rest_api, '', 'bob') == (we_list[0], None)
    assert helper.get_working_environment_details_by_name(rest_api, '', 'bob') == (we_list[0], None)
    assert helper.get_working_environment_details_by_name(rest_api, '', 'bob') == (we_list[0], None)
    error = "get_working_environment_details_by_name: Working environment not found"
    assert helper.get_working_environment_details_by_name(rest_api, '', 'bob') == (None, error)


@patch('requests.request')
def test_get_working_environment_details(mock_request):
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data={'key': [{'a': 'b'}]}, status_code=200),
        mockResponse(json_data={'key': [{'c': 'd'}]}, status_code=500)
    ]
    helper = NetAppModule()
    args = dict(mock_args())
    rest_api = create_restapi_object(args)
    helper.parameters['working_environment_id'] = 'test_we'
    assert helper.get_working_environment_details(rest_api, '') == ({'key': [{'a': 'b'}]}, None)
    error = "Error: get_working_environment_details 500"
    assert helper.get_working_environment_details(rest_api, '') == (None, error)


@patch('requests.request')
def test_get_working_environment_detail_for_snapmirror(mock_request):
    json_data = {'onPremWorkingEnvironments': [],
                 'gcpVsaWorkingEnvironments': [],
                 'azureVsaWorkingEnvironments': [],
                 'vsaWorkingEnvironments': []
                 }
    json_data_source = dict(json_data)
    json_data_source['onPremWorkingEnvironments'] = [{'name': 'test_we_s'}]
    json_data_destination = dict(json_data)
    json_data_destination['onPremWorkingEnvironments'] = [{'name': 'test_we_d'}]
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),    # OAUTH
        # by id, first test
        mockResponse(json_data={'key': [{'publicId': 'test_we_s'}]}, status_code=200),  # env details source
        mockResponse(json_data={'key': [{'publicId': 'test_we_d'}]}, status_code=200),  # env details dest
        # by id, second test
        mockResponse(json_data={'key': [{'c': 'd'}]}, status_code=500),                 # error source
        # by id, third test
        mockResponse(json_data={'key': [{'publicId': 'test_we_s'}]}, status_code=200),  # env details source
        mockResponse(json_data={'key': [{'e': 'f'}]}, status_code=500),                 # error source
        # by name, first test
        mockResponse(json_data={'a': 'b'}, status_code=200),                            # exists source
        mockResponse(json_data=json_data_source, status_code=200),                      # env details source
        mockResponse(json_data={'a': 'b'}, status_code=200),                            # exists dest
        mockResponse(json_data=json_data_destination, status_code=200),                 # env details dest
        # by name, second test
        mockResponse(json_data={'key': {'c': 'd'}}, status_code=500),                   # error source
        # by name, third test
        mockResponse(json_data={'a': 'b'}, status_code=200),                            # exists source
        mockResponse(json_data=json_data_source, status_code=200),                      # env details source
        mockResponse(json_data={'key': {'e': 'f'}}, status_code=500),                   # error source
    ]
    helper = NetAppModule()
    args = dict(mock_args())
    rest_api = create_restapi_object(args)
    # search by id
    helper.parameters['source_working_environment_id'] = 'test_we_s'
    helper.parameters['destination_working_environment_id'] = 'test_we_d'
    assert helper.get_working_environment_detail_for_snapmirror(rest_api, '') == ({'publicId': 'test_we_s'}, {'publicId': 'test_we_d'}, None)
    error = "Error getting WE info: 500: {'key': [{'c': 'd'}]}"
    assert helper.get_working_environment_detail_for_snapmirror(rest_api, '') == (None, None, error)
    error = "Error getting WE info: 500: {'key': [{'e': 'f'}]}"
    assert helper.get_working_environment_detail_for_snapmirror(rest_api, '') == (None, None, error)
    # search by name
    del helper.parameters['source_working_environment_id']
    del helper.parameters['destination_working_environment_id']
    helper.parameters['source_working_environment_name'] = 'test_we_s'
    helper.parameters['destination_working_environment_name'] = 'test_we_d'
    assert helper.get_working_environment_detail_for_snapmirror(rest_api, '') == ({'name': 'test_we_s'}, {'name': 'test_we_d'}, None)
    error = '500'
    assert helper.get_working_environment_detail_for_snapmirror(rest_api, '') == (None, None, error)
    error = '500'
    assert helper.get_working_environment_detail_for_snapmirror(rest_api, '') == (None, None, error)
    # no destination id nor name
    del helper.parameters['destination_working_environment_name']
    error = 'Cannot find working environment by destination_working_environment_id or destination_working_environment_name'
    assert helper.get_working_environment_detail_for_snapmirror(rest_api, '') == (None, None, error)
    # no source id nor name
    del helper.parameters['source_working_environment_name']
    error = 'Cannot find working environment by source_working_environment_id or source_working_environment_name'
    assert helper.get_working_environment_detail_for_snapmirror(rest_api, '') == (None, None, error)


def test_create_account():
    helper = NetAppModule()
    error = "Error: creating an account is not supported."
    assert helper.create_account("rest_api") == (None, error)


@patch('requests.request')
def test_get_or_create_account(mock_request):
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data=[{'accountPublicId': 'account_id'}], status_code=200),
        mockResponse(json_data=[], status_code=200),
        mockResponse(json_data={'c': 'd'}, status_code=500)
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    assert helper.get_or_create_account(rest_api) == ('account_id', None)
    error = 'Error: account cannot be located - check credentials or provide account_id.'
    assert helper.get_or_create_account(rest_api) == (None, error)
    error = '500'
    assert helper.get_or_create_account(rest_api) == (None, error)


@patch('requests.request')
def test_get_account_info(mock_request):
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data=[{'accountPublicId': 'account_id'}], status_code=200),
        mockResponse(json_data=[], status_code=200),
        mockResponse(json_data={'c': 'd'}, status_code=500)
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    assert helper.get_account_info(rest_api, '') == ([{'accountPublicId': 'account_id'}], None)
    assert helper.get_account_info(rest_api, '') == ([], None)
    assert helper.get_account_info(rest_api, '') == (None, '500')


@patch('requests.request')
def test_get_account_id(mock_request):
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data=[{'accountPublicId': 'account_id'}], status_code=200),
        mockResponse(json_data=[], status_code=200),
        mockResponse(json_data={'c': 'd'}, status_code=500)
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    assert helper.get_account_id(rest_api) == ('account_id', None)
    error = 'Error: no account found - check credentials or provide account_id.'
    assert helper.get_account_id(rest_api) == (None, error)
    error = '500'
    assert helper.get_account_id(rest_api) == (None, error)


@patch('requests.request')
def test_get_accounts_info(mock_request):
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data=[{'accountPublicId': 'account_id'}], status_code=200),
        mockResponse(json_data={'c': 'd'}, status_code=500)
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    assert helper.get_accounts_info(rest_api, '') == ([{'accountPublicId': 'account_id'}], None)
    error = '500'
    assert helper.get_accounts_info(rest_api, '') == (None, error)


def test_set_api_root_path():
    helper = NetAppModule()
    helper.parameters['working_environment_id'] = 'abc'
    working_environment_details = {'cloudProviderName': 'Amazon', 'isHA': False}
    helper.set_api_root_path(working_environment_details, helper)
    assert helper.api_root_path == '/occm/api/vsa'
    working_environment_details = {'cloudProviderName': 'Other', 'isHA': False}
    helper.set_api_root_path(working_environment_details, helper)
    assert helper.api_root_path == '/occm/api/other/vsa'
    working_environment_details = {'cloudProviderName': 'Other', 'isHA': True}
    helper.set_api_root_path(working_environment_details, helper)
    assert helper.api_root_path == '/occm/api/other/ha'


@patch('requests.request')
def test_get_occm_agents_by_account(mock_request):
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data=[{'a': 'b'}], status_code=200),
        mockResponse(json_data=[{'c': 'd'}], status_code=500)
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    assert helper.get_occm_agents_by_account(rest_api, '') == ([{'a': 'b'}], None)
    error = '500'
    assert helper.get_occm_agents_by_account(rest_api, '') == ([{'c': 'd'}], error)


@patch('requests.request')
def test_get_occm_agents_by_name(mock_request):
    json_data = {'agents':
                 [{'name': '', 'provider': ''},
                  {'name': 'a1', 'provider': 'p1'},
                  {'name': 'a1', 'provider': 'p1'},
                  {'name': 'a1', 'provider': 'p2'},
                  {'name': 'a2', 'provider': 'p1'},
                  ]}
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data=json_data, status_code=200),
        mockResponse(json_data=json_data, status_code=500)
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    expected = [agent for agent in json_data['agents'] if agent['name'] == 'a1' and agent['provider'] == 'p1']
    assert helper.get_occm_agents_by_name(rest_api, 'account', 'a1', 'p1') == (expected, None)
    error = '500'
    assert helper.get_occm_agents_by_name(rest_api, 'account', 'a1', 'p1') == (expected, error)


@patch('requests.request')
def test_get_agents_info(mock_request):
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data=[{'accountPublicId': 'account_id'}], status_code=200),   # get account_id
        mockResponse(json_data=[{'a': 'b'}], status_code=200),
        mockResponse(json_data=[{'accountPublicId': 'account_id'}], status_code=200),   # get account_id
        mockResponse(json_data=[{'c': 'd'}], status_code=500),
        mockResponse(json_data=[{'accountPublicId': 'account_id'}], status_code=400),   # get account_id
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    assert helper.get_agents_info(rest_api, '') == ([{'a': 'b'}], None)
    error = '500'
    assert helper.get_agents_info(rest_api, '') == ([{'c': 'd'}], error)
    error = '400'
    assert helper.get_agents_info(rest_api, '') == (None, error)


@patch('requests.request')
def test_get_active_agents_info(mock_request):
    json_data = {'agents':
                 [{'name': '', 'provider': '', 'agentId': 1, 'status': ''},
                  {'name': 'a1', 'provider': 'p1', 'agentId': 1, 'status': 'active'},
                  {'name': 'a1', 'provider': 'p1', 'agentId': 1, 'status': ''},
                  {'name': 'a1', 'provider': 'p2', 'agentId': 1, 'status': 'active'},
                  {'name': 'a2', 'provider': 'p1', 'agentId': 1, 'status': 'active'},
                  ]}
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data=[{'accountPublicId': 'account_id'}], status_code=200),   # get account_id
        mockResponse(json_data=json_data, status_code=200),
        mockResponse(json_data=[{'accountPublicId': 'account_id'}], status_code=200),   # get account_id
        mockResponse(json_data=json_data, status_code=500),
        mockResponse(json_data=[{'accountPublicId': 'account_id'}], status_code=400),   # get account_id
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    active = [agent for agent in json_data['agents'] if agent['status'] == 'active']
    expected = [{'name': agent['name'], 'client_id': agent['agentId'], 'provider': agent['provider']} for agent in active]
    assert helper.get_active_agents_info(rest_api, '') == (expected, None)
    error = '500'
    assert helper.get_active_agents_info(rest_api, '') == (expected, error)
    error = '400'
    assert helper.get_active_agents_info(rest_api, '') == (None, error)


@patch('requests.request')
def test_get_occm_agent_by_id(mock_request):
    json_data = {'agent':
                 {'name': 'a1', 'provider': 'p1', 'agentId': 1, 'status': 'active'}
                 }
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data=json_data, status_code=200),
        mockResponse(json_data=json_data, status_code=500),
        mockResponse(json_data={'a': 'b'}, status_code=500),
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    expected = json_data['agent']
    assert helper.get_occm_agent_by_id(rest_api, '') == (expected, None)
    error = '500'
    assert helper.get_occm_agent_by_id(rest_api, '') == (expected, error)
    assert helper.get_occm_agent_by_id(rest_api, '') == ({'a': 'b'}, error)


@patch('requests.request')
def test_check_occm_status(mock_request):
    json_data = {'agent':
                 {'name': 'a1', 'provider': 'p1', 'agentId': 1, 'status': 'active'}
                 }
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data=json_data, status_code=200),
        mockResponse(json_data=json_data, status_code=500)
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    expected = json_data
    assert helper.check_occm_status(rest_api, '') == (expected, None)
    error = '500'
    assert helper.check_occm_status(rest_api, '') == (expected, error)


@patch('requests.request')
def test_register_agent_to_service(mock_request):
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data={}, status_code=200),
        mockResponse(json_data={}, status_code=200),
        mockResponse(json_data={}, status_code=500)
    ]
    helper = NetAppModule()
    rest_api = create_restapi_object(mock_args())
    helper.parameters['account_id'] = 'account_id'
    helper.parameters['company'] = 'company'
    helper.parameters['region'] = 'region'
    helper.parameters['subnet_id'] = 'subnet_id'
    expected = {}
    assert helper.register_agent_to_service(rest_api, 'provider', 'vpc') == (expected, None)
    args, kwargs = mock_request.call_args
    body = kwargs['json']
    assert 'placement' in body
    assert 'network' in body['placement']
    assert body['placement']['network'] == 'vpc'
    body_other = body
    assert helper.register_agent_to_service(rest_api, 'AWS', 'vpc') == (expected, None)
    args, kwargs = mock_request.call_args
    body = kwargs['json']
    assert 'placement' in body
    assert 'network' in body['placement']
    assert body['placement']['network'] == 'vpc'
    assert body_other != body
    body['placement']['provider'] = 'provider'
    assert body_other == body
    error = '500'
    assert helper.register_agent_to_service(rest_api, 'provider', 'vpc') == (expected, error)


@patch('requests.request')
def test_delete_occm(mock_request):
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data={'result': 'any'}, status_code=200),
        mockResponse(json_data={'result': 'any'}, status_code=500),
    ]
    helper = NetAppModule()
    helper.parameters['account_id'] = 'account_id'
    rest_api = create_restapi_object(mock_args())
    assert helper.delete_occm(rest_api, '') == ({'result': 'any'}, None)
    error = '500'
    assert helper.delete_occm(rest_api, '') == ({'result': 'any'}, error)


@patch('requests.request')
def test_delete_occm_agents(mock_request):
    agents = [{'agentId': 'a1'},
              {'agentId': 'a2'}]
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),    # OAUTH
        mockResponse(json_data={'result': 'any'}, status_code=200),    # a1
        mockResponse(json_data={'result': 'any'}, status_code=200),    # a2
        mockResponse(json_data={'result': 'any'}, status_code=500),    # a1
        mockResponse(json_data={'result': 'any'}, status_code=200),    # a2
        mockResponse(json_data={'result': 'any'}, status_code=200),    # a1
        mockResponse(json_data={'result': 'any'}, status_code=200),    # a2
    ]
    helper = NetAppModule()
    helper.parameters['account_id'] = 'account_id'
    rest_api = create_restapi_object(mock_args())
    assert helper.delete_occm_agents(rest_api, agents) == []
    error = '500'
    assert helper.delete_occm_agents(rest_api, agents) == [({'result': 'any'}, error)]
    agents.append({'a': 'b'})
    error = "unexpected agent contents: {'a': 'b'}"
    assert helper.delete_occm_agents(rest_api, agents) == [(None, error)]


@patch('requests.request')
def test_get_tenant(mock_request):
    tenants = [{'publicId': 'a1'},
               {'publicId': 'a2'}]
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),            # OAUTH
        mockResponse(json_data=tenants, status_code=200),               # get success
        mockResponse(json_data={'result': 'any'}, status_code=500),     # get error
    ]
    helper = NetAppModule()
    # helper.parameters['account_id'] = 'account_id'
    rest_api = create_restapi_object(mock_args())
    assert helper.get_tenant(rest_api, '') == ('a1', None)
    error = "Error: unexpected response on getting tenant for cvo: 500, {'result': 'any'}"
    assert helper.get_tenant(rest_api, '') == (None, error)
