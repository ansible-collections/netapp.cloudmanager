# (c) 2022, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests Cloudmanager Ansible module: '''

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import json
import sys
import pytest

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.cloudmanager.tests.unit.compat import unittest
from ansible_collections.netapp.cloudmanager.tests.unit.compat.mock import patch
import ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_aws_fsx \
    import NetAppCloudManagerAWSFSX as my_module

if not netapp_utils.HAS_REQUESTS and sys.version_info < (3, 5):
    pytestmark = pytest.mark.skip('skipping as missing required imports on 2.6 and 2.7')


def set_module_args(args):
    '''prepare arguments so that they will be picked up during module creation'''
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    '''Exception class to be raised by module.exit_json and caught by the test case'''


class AnsibleFailJson(Exception):
    '''Exception class to be raised by module.fail_json and caught by the test case'''


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    '''function to patch over exit_json; package return data into an exception'''
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    '''function to patch over fail_json; package return data into an exception'''
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args_pass_check(self):
        return dict({
            'state': 'present',
            'name': 'TestA',
            'workspace_id': 'test',
            'region': 'us-west-1',
            'tenant_id': 'account-test',
            'storage_capacity_size': 1024,
            'throughput_capacity': 512,
            'storage_capacity_size_unit': 'TiB',
            'aws_credentials_name': 'test',
            'primary_subnet_id': 'test',
            'secondary_subnet_id': 'test',
            'fsx_admin_password': 'password',
            'refresh_token': 'myrefresh_token',
        })

    def set_args_create_cloudmanager_aws_fsx(self):
        return dict({
            'state': 'present',
            'name': 'TestA',
            'workspace_id': 'test',
            'region': 'us-west-1',
            'tenant_id': 'account-test',
            'storage_capacity_size': 1024,
            'storage_capacity_size_unit': 'TiB',
            'throughput_capacity': 512,
            'aws_credentials_name': 'test',
            'primary_subnet_id': 'test',
            'secondary_subnet_id': 'test',
            'fsx_admin_password': 'password',
            'refresh_token': 'myrefresh_token',
        })

    def set_args_delete_cloudmanager_aws_fsx(self):
        return dict({
            'state': 'absent',
            'name': 'Dummyname',
            'tenant_id': 'account-test',
            'refresh_token': 'myrefresh_token',
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_aws_fsx.NetAppCloudManagerAWSFSX.get_aws_credentials_id')
    def test_module_fail_when_required_args_present(self, get_aws_credentials_id, get_token):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            get_aws_credentials_id.return_value = '123', None
            get_token.return_value = 'test', 'test'
            my_module()
            exit_json(changed=True, msg="TestCase Fail when required args are present")
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_aws_fsx_details')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_aws_fsx.NetAppCloudManagerAWSFSX.wait_on_completion_for_fsx')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_aws_fsx.NetAppCloudManagerAWSFSX.check_task_status_for_fsx')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_aws_fsx.NetAppCloudManagerAWSFSX.get_aws_credentials_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    def test_create_cloudmanager_aws_fsx_pass(self, get_post_api, get_aws_credentials_id, check_task_status_for_fsx,
                                              wait_on_completion_for_fsx, get_aws_fsx_details, get_token):
        set_module_args(self.set_args_create_cloudmanager_aws_fsx())
        get_token.return_value = 'test', 'test'
        get_aws_credentials_id.return_value = '123', None
        my_obj = my_module()

        response = {'id': 'abcdefg12345'}
        get_post_api.return_value = response, None, None
        check_task_status_for_fsx.return_value = {'providerDetails': {'status': {'status': 'ON', 'lifecycle': 'AVAILABLE'}}}, None
        wait_on_completion_for_fsx.return_value = None
        get_aws_fsx_details.return_value = None, None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_cloudmanager_aws_fsx_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_aws_fsx_details')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.delete')
    def test_delete_cloudmanager_aws_fsx_pass(self, get_delete_api, get_aws_fsx_details, get_token):
        set_module_args(self.set_args_delete_cloudmanager_aws_fsx())
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        my_fsx = {
            'name': 'test',
            'id': 'test'}
        get_aws_fsx_details.return_value = my_fsx, None
        get_delete_api.return_value = None, None, None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_delete_cloudmanager_aws_fsx_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
