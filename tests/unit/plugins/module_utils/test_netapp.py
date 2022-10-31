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
import pytest
import sys
try:
    import requests.exceptions
    HAS_REQUESTS_EXC = True
except ImportError:
    HAS_REQUESTS_EXC = False

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.cloudmanager.tests.unit.compat.mock import patch
from ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp import CloudManagerRestAPI
import ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp as netapp_utils

if (not netapp_utils.HAS_REQUESTS or not HAS_REQUESTS_EXC) and sys.version_info < (3, 5):
    pytestmark = pytest.mark.skip('skipping as missing required imports on 2.6 and 2.7')


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class MockModule():
    ''' rough mock for an Ansible module class '''
    def __init__(self):
        self.params = {}

    def fail_json(self, *args, **kwargs):  # pylint: disable=unused-argument
        """function to simulate fail_json: package return data into an exception"""
        kwargs['failed'] = True
        raise AnsibleFailJson(kwargs)


class mockResponse:
    def __init__(self, json_data, status_code, headers=None, raise_action=None):
        self.json_data = json_data
        self.status_code = status_code
        self.content = json_data
        self.headers = headers or {}
        self.raise_action = raise_action

    def raise_for_status(self):
        pass

    def json(self):
        if self.raise_action == 'bad_json':
            raise ValueError(self.raise_action)
        return self.json_data


def create_module(args):
    argument_spec = netapp_utils.cloudmanager_host_argument_spec()
    set_module_args(args)
    module = basic.AnsibleModule(argument_spec)
    module.fail_json = fail_json
    return module


def create_restapi_object(args):
    module = create_module(args)
    return netapp_utils.CloudManagerRestAPI(module)


def mock_args(feature_flags=None, client_id=None):
    args = {
        'refresh_token': 'ABCDEFGS'
    }
    if feature_flags is not None:
        args['feature_flags'] = feature_flags
    if client_id is not None:
        args['client_id'] = client_id
    return args


TOKEN_DICT = {
    'access_token': 'access_token',
    'token_type': 'token_type'
}


def test_missing_params():
    module = MockModule()
    with pytest.raises(KeyError) as exc:
        netapp_utils.CloudManagerRestAPI(module)
    assert exc.match('refresh_token')


@patch('requests.request')
def test_get_token_refresh(mock_request):
    ''' successfully get token using refresh token '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
    ]
    # get_token is called when the object is created
    rest_api = create_restapi_object(mock_args())
    print(rest_api.token_type, rest_api.token)
    assert rest_api.token_type == TOKEN_DICT['token_type']
    assert rest_api.token == TOKEN_DICT['access_token']


@patch('requests.request')
def test_negative_get_token_none(mock_request):
    ''' missing refresh token and Service Account '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
    ]
    # get_token is called when the object is created
    args = dict(mock_args())
    args.pop('refresh_token')
    # get_token is called when the object is created
    with pytest.raises(AnsibleFailJson) as exc:
        rest_api = create_restapi_object(args)
    msg = 'Missing refresh_token or sa_client_id and sa_secret_key'
    assert msg in exc.value.args[0]['msg']


@patch('requests.request')
def test_get_token_sa(mock_request):
    ''' successfully get token using Service Account '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
    ]
    # get_token is called when the object is created
    args = dict(mock_args())
    args.pop('refresh_token')
    args['sa_client_id'] = '123'
    args['sa_secret_key'] = 'a1b2c3'
    rest_api = create_restapi_object(args)
    print(rest_api.token_type, rest_api.token)
    assert rest_api.token_type == TOKEN_DICT['token_type']
    assert rest_api.token == TOKEN_DICT['access_token']


@patch('requests.request')
def test_negative_get_token(mock_request):
    ''' error on OAUTH request '''
    mock_request.side_effect = [
        mockResponse(json_data={'message': 'error message'}, status_code=206)
    ]
    # get_token is called when the object is created
    with pytest.raises(AnsibleFailJson) as exc:
        rest_api = create_restapi_object(mock_args())
    msg = 'Error acquiring token: error message'
    assert msg in exc.value.args[0]['msg']


@patch('requests.request')
def test_get_json(mock_request):
    ''' get with no data '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data={'key': 'value'}, status_code=200, headers={'OnCloud-Request-Id': 'OCR_id'})
    ]
    rest_api = create_restapi_object(mock_args())
    message, error, ocr = rest_api.get('api', None)
    print(message, error, ocr)
    assert message == {'key': 'value'}
    assert error is None
    assert ocr == 'OCR_id'


@patch('time.sleep')
@patch('requests.request')
def test_get_retries(mock_request, dont_sleep):
    ''' get with no data '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        requests.exceptions.ConnectionError('Max retries exceeded with url:'),
        requests.exceptions.ConnectionError('Max retries exceeded with url:'),
        mockResponse(json_data={'key': 'value'}, status_code=200, headers={'OnCloud-Request-Id': 'OCR_id'})
    ]
    rest_api = create_restapi_object(mock_args())
    message, error, ocr = rest_api.get('api', None)
    print(message, error, ocr)
    assert message == {'key': 'value'}
    assert error is None
    assert ocr == 'OCR_id'


@patch('time.sleep')
@patch('requests.request')
def test_get_retries_exceeded(mock_request, dont_sleep):
    ''' get with no data '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        requests.exceptions.ConnectionError('Max retries exceeded with url:'),
        requests.exceptions.ConnectionError('Max retries exceeded with url:'),
        requests.exceptions.ConnectionError('Max retries exceeded with url:'),
        mockResponse(json_data={'key': 'value'}, status_code=200, headers={'OnCloud-Request-Id': 'OCR_id'})
    ]
    rest_api = create_restapi_object(mock_args())
    message, error, ocr = rest_api.get('api', None)
    print(message, error, ocr)
    assert 'Max retries exceeded with url:' in error


@patch('requests.request')
def test_empty_get_sent_bad_json(mock_request):
    ''' get with invalid json '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data='anything', status_code=200, raise_action='bad_json')
    ]
    rest_api = create_restapi_object(mock_args())
    message, error, ocr = rest_api.get('api', None)
    print(message, error, ocr)
    assert message is None
    assert error is None
    assert ocr is None


@patch('requests.request')
def test_empty_get_sent_203(mock_request):
    ''' get with no data and 203 status code '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data={}, status_code=203)
    ]
    rest_api = create_restapi_object(mock_args())
    message, error, ocr = rest_api.get('api', None)
    print(message, error, ocr)
    assert message == {}
    assert error is None
    assert ocr is None


@patch('requests.request')
def test_negative_get_sent_203(mock_request):
    ''' get with 203 status code - not sure we should error out here '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data={'message': 'error message'}, status_code=203)
    ]
    rest_api = create_restapi_object(mock_args())
    message, error, ocr = rest_api.get('api', None)
    print(message, error, ocr)
    assert message == {'message': 'error message'}
    assert error == 'error message'
    assert ocr is None


@patch('requests.request')
def test_negative_get_sent_300(mock_request):
    ''' get with 300 status code - 300 indicates an error '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        mockResponse(json_data={}, status_code=300)
    ]
    rest_api = create_restapi_object(mock_args())
    message, error, ocr = rest_api.get('api', None)
    print(message, error, ocr)
    assert message == {}
    assert error == '300'
    assert ocr is None


@patch('requests.request')
def test_negative_get_raise_http_exc(mock_request):
    ''' get with HTTPError exception '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        requests.exceptions.HTTPError('some exception')
    ]
    rest_api = create_restapi_object(mock_args())
    message, error, ocr = rest_api.get('api', None)
    print(message, error, ocr)
    assert message is None
    assert error == 'some exception'
    assert ocr is None


@patch('requests.request')
def test_negative_get_raise_conn_exc(mock_request):
    ''' get with ConnectionError exception '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        requests.exceptions.ConnectionError('some exception')
    ]
    rest_api = create_restapi_object(mock_args())
    message, error, ocr = rest_api.get('api', None)
    print(message, error, ocr)
    assert message is None
    assert error == 'some exception'
    assert ocr is None


@patch('requests.request')
def test_negative_get_raise_oserror_exc(mock_request):
    ''' get with a general exception '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        OSError('some exception')
    ]
    rest_api = create_restapi_object(mock_args())
    message, error, ocr = rest_api.get('api', None)
    print(message, error, ocr)
    assert message is None
    assert error == 'some exception'
    assert ocr is None


def test_has_feature_success_default():
    ''' existing feature_flag with default '''
    flag = 'show_modified'
    module = create_module(mock_args())
    value = netapp_utils.has_feature(module, flag)
    assert value


def test_has_feature_success_user_true():
    ''' existing feature_flag with value set to True '''
    flag = 'user_deprecation_warning'
    args = dict(mock_args({flag: True}))
    module = create_module(args)
    value = netapp_utils.has_feature(module, flag)
    assert value


def test_has_feature_success_user_false():
    ''' existing feature_flag with value set to False '''
    flag = 'user_deprecation_warning'
    args = dict(mock_args({flag: False}))
    print(args)
    module = create_module(args)
    value = netapp_utils.has_feature(module, flag)
    assert not value


def test_has_feature_invalid_key():
    ''' existing feature_flag with unknown key '''
    flag = 'deprecation_warning_bad_key'
    module = create_module(mock_args())
    with pytest.raises(AnsibleFailJson) as exc:
        netapp_utils.has_feature(module, flag)
    msg = 'Internal error: unexpected feature flag: %s' % flag
    assert exc.value.args[0]['msg'] == msg


def test_has_feature_invalid_bool():
    ''' existing feature_flag with non boolean value '''
    flag = 'deprecation_warning_key'
    module = create_module(mock_args({flag: 'str'}))
    with pytest.raises(AnsibleFailJson) as exc:
        netapp_utils.has_feature(module, flag)
    msg = "Error: expected bool type for feature flag"
    assert msg in exc.value.args[0]['msg']


STATUS_DICT = {
    'status': 1,
    'error': None
}


@patch('time.sleep')
@patch('requests.request')
def test_check_task_status(mock_request, mock_sleep):
    ''' successful get with 2 retries '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        OSError('some exception'),
        requests.exceptions.ConnectionError('some exception'),
        mockResponse(json_data=STATUS_DICT, status_code=200)
    ]
    rest_api = create_restapi_object(mock_args())
    rest_api.module.params['client_id'] = '123'
    status, error_msg, error = rest_api.check_task_status('api')
    assert status == STATUS_DICT['status']
    assert error_msg == STATUS_DICT['error']
    assert error is None


@patch('time.sleep')
@patch('requests.request')
def test_negative_check_task_status(mock_request, mock_sleep):
    ''' get with 4 failed retries '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        OSError('some exception'),
        requests.exceptions.ConnectionError('some exception'),
        requests.exceptions.ConnectionError('some exception'),
        requests.exceptions.HTTPError('some exception'),
    ]
    rest_api = create_restapi_object(mock_args())
    rest_api.module.params['client_id'] = '123'
    status, error_msg, error = rest_api.check_task_status('api')
    assert status == 0
    assert error_msg == ''
    assert error == 'some exception'


@patch('time.sleep')
@patch('requests.request')
def test_wait_on_completion(mock_request, mock_sleep):
    ''' successful get with 2 retries '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        OSError('some exception'),
        requests.exceptions.ConnectionError('some exception'),
        mockResponse(json_data=STATUS_DICT, status_code=200)
    ]
    rest_api = create_restapi_object(mock_args())
    rest_api.module.params['client_id'] = '123'
    error = rest_api.wait_on_completion('api', 'action', 'task', 2, 1)
    assert error is None


@patch('time.sleep')
@patch('requests.request')
def test_negative_wait_on_completion_failure(mock_request, mock_sleep):
    ''' successful get with 2 retries, but status is -1 '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        OSError('some exception'),
        requests.exceptions.ConnectionError('some exception'),
        mockResponse(json_data={'status': -1, 'error': 'task_error'}, status_code=200)
    ]
    rest_api = create_restapi_object(mock_args())
    rest_api.module.params['client_id'] = '123'
    error = rest_api.wait_on_completion('api', 'action', 'task', 2, 1)
    assert error == 'Failed to task action, error: task_error'


@patch('time.sleep')
@patch('requests.request')
def test_negative_wait_on_completion_error(mock_request, mock_sleep):
    ''' get with 4 failed retries '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        OSError('some exception'),
        requests.exceptions.ConnectionError('some exception'),
        requests.exceptions.ConnectionError('some exception'),
        requests.exceptions.HTTPError('some http exception'),
    ]
    rest_api = create_restapi_object(mock_args())
    rest_api.module.params['client_id'] = '123'
    error = rest_api.wait_on_completion('api', 'action', 'task', 2, 1)
    assert error == 'some http exception'


@patch('time.sleep')
@patch('requests.request')
def test_negative_wait_on_completion_timeout(mock_request, mock_sleep):
    ''' successful get with 2 retries, but status is 0 '''
    mock_request.side_effect = [
        mockResponse(json_data=TOKEN_DICT, status_code=200),  # OAUTH
        OSError('some exception'),
        requests.exceptions.ConnectionError('some exception'),
        mockResponse(json_data={'status': 0, 'error': 'task_error'}, status_code=200),
        mockResponse(json_data={'status': 0, 'error': 'task_error'}, status_code=200),
        mockResponse(json_data={'status': 0, 'error': 'task_error'}, status_code=200)
    ]
    rest_api = create_restapi_object(mock_args())
    rest_api.module.params['client_id'] = '123'
    error = rest_api.wait_on_completion('api', 'action', 'task', 2, 1)
    assert error == 'Taking too long for action to task or not properly setup'
