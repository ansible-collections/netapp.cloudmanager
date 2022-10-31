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
from ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_snapmirror \
    import NetAppCloudmanagerSnapmirror as my_module

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
            'source_working_environment_name': 'TestA',
            'destination_working_environment_name': 'TestB',
            'source_volume_name': 'source',
            'destination_volume_name': 'dest',
            'source_svm_name': 'source_svm',
            'destination_svm_name': 'dest_svm',
            'policy': 'MirrorAllSnapshots',
            'schedule': 'min',
            'max_transfer_rate': 102400,
            'client_id': 'client_id',
            'refresh_token': 'myrefresh_token',
        })

    def set_args_create_cloudmanager_snapmirror(self):
        return dict({
            'state': 'present',
            'source_working_environment_name': 'TestA',
            'destination_working_environment_name': 'TestB',
            'source_volume_name': 'source',
            'destination_volume_name': 'dest',
            'source_svm_name': 'source_svm',
            'destination_svm_name': 'dest_svm',
            'policy': 'MirrorAllSnapshots',
            'schedule': 'min',
            'max_transfer_rate': 102400,
            'client_id': 'client_id',
            'refresh_token': 'myrefresh_token',
        })

    def set_args_delete_cloudmanager_snapmirror(self):
        return dict({
            'state': 'absent',
            'source_working_environment_name': 'TestA',
            'destination_working_environment_name': 'TestB',
            'source_volume_name': 'source',
            'destination_volume_name': 'dest',
            'client_id': 'client_id',
            'refresh_token': 'myrefresh_token',
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    def test_module_fail_when_required_args_present(self, get_token):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleExitJson) as exc:
            set_module_args(self.set_default_args_pass_check())
            get_token.return_value = 'test', 'test'
            my_module()
            exit_json(changed=True, msg="TestCase Fail when required args are present")
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_working_environment_detail_for_snapmirror')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.wait_on_completion')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_snapmirror.NetAppCloudmanagerSnapmirror.get_snapmirror')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_snapmirror.NetAppCloudmanagerSnapmirror.build_quote_request')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_snapmirror.NetAppCloudmanagerSnapmirror.quote_volume')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_snapmirror.NetAppCloudmanagerSnapmirror.get_volumes')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_snapmirror.NetAppCloudmanagerSnapmirror.get_interclusterlifs')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.send_request')
    def test_create_cloudmanager_snapmirror_create_pass(self, send_request, get_interclusterlifs, get_volumes, quote_volume, build_quote_request,
                                                        get_snapmirror, wait_on_completion, get_working_environment_detail_for_snapmirror, get_token):
        set_module_args(self.set_args_create_cloudmanager_snapmirror())
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        response = {'id': 'abcdefg12345'}
        source_we_info = {'publicId': 'test1', 'workingEnvironmentType': 'AMAZON'}
        dest_we_info = {'publicId': 'test2', 'workingEnvironmentType': 'AMAZON', 'svmName': 'source_svm', 'name': 'TestB'}
        source_vol = [{'name': 'source', 'svmName': 'source_svm', 'providerVolumeType': 'abc'}]
        quote_volume_response = {'numOfDisks': 10, 'aggregateName': 'aggr1'}
        interclusterlifs_resp = {'interClusterLifs': [{'address': '10.10.10.10'}], 'peerInterClusterLifs': [{'address': '10.10.10.10'}]}
        get_working_environment_detail_for_snapmirror.return_value = source_we_info, dest_we_info, None
        send_request.return_value = response, None, None
        wait_on_completion.return_value = None
        get_snapmirror.return_value = None
        get_volumes.return_value = source_vol
        build_quote_request.return_value = {'name': 'test'}
        quote_volume.return_value = quote_volume_response
        get_interclusterlifs.return_value = interclusterlifs_resp

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_cloudmanager_snapmirror_create_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_snapmirror.NetAppCloudmanagerSnapmirror.get_snapmirror')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.send_request')
    def test_delete_cloudmanager_snapmirror_delete_pass(self, send_request, get_snapmirror, get_token):
        set_module_args(self.set_args_delete_cloudmanager_snapmirror())
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        my_snapmirror = {
            'source_working_environment_id': '456',
            'destination_svm_name': 'dest_svm',
            'destination_working_environment_id': '123'}
        get_snapmirror.return_value = my_snapmirror
        send_request.return_value = None, None, None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_delete_cloudmanager_snapmirror_delete_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
