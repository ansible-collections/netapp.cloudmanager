# (c) 2021, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests Cloudmanager Ansible module: '''

from __future__ import (absolute_import, division, print_function)
from logging import exception

__metaclass__ = type

import json
import sys
import pytest

HAS_BOTOCORE = True
try:
    from botocore.exceptions import ClientError
except ImportError:
    HAS_BOTOCORE = False

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.cloudmanager.tests.unit.compat import unittest
from ansible_collections.netapp.cloudmanager.tests.unit.compat.mock import patch

from ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws \
    import NetAppCloudManagerConnectorAWS as my_module, IMPORT_EXCEPTION, main as my_main

if IMPORT_EXCEPTION is not None and sys.version_info < (3, 5):
    pytestmark = pytest.mark.skip('skipping as missing required imports on 2.6 and 2.7: %s' % IMPORT_EXCEPTION)


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
            'region': 'us-west-1',
            'key_name': 'dev_automation',
            'subnet_id': 'subnet-test',
            'ami': 'ami-test',
            'security_group_ids': ['sg-test'],
            'refresh_token': 'myrefresh_token',
            'iam_instance_profile_name': 'OCCM_AUTOMATION',
            'account_id': 'account-test',
            'company': 'NetApp'
        })

    def set_args_create_cloudmanager_connector_aws(self):
        return dict({
            'state': 'present',
            'name': 'Dummyname',
            'region': 'us-west-1',
            'key_name': 'dev_automation',
            'subnet_id': 'subnet-test',
            'ami': 'ami-test',
            'security_group_ids': ['sg-test'],
            'refresh_token': 'myrefresh_token',
            'iam_instance_profile_name': 'OCCM_AUTOMATION',
            'account_id': 'account-test',
            'company': 'NetApp'
        })

    def set_args_delete_cloudmanager_connector_aws(self):
        return dict({
            'state': 'absent',
            'name': 'Dummyname',
            'client_id': 'test',
            'instance_id': 'test',
            'region': 'us-west-1',
            'account_id': 'account-test',
            'refresh_token': 'myrefresh_token',
            'company': 'NetApp'
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
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws.NetAppCloudManagerConnectorAWS.get_instance')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws.NetAppCloudManagerConnectorAWS.create_instance')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws.NetAppCloudManagerConnectorAWS.get_vpc')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws.NetAppCloudManagerConnectorAWS.register_agent_to_service')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws.NetAppCloudManagerConnectorAWS.get_ami')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    def test_create_cloudmanager_connector_aws_pass(self, get_post_api, get_ami, register_agent_to_service, get_vpc, create_instance, get_instance, get_token):
        set_module_args(self.set_args_create_cloudmanager_connector_aws())
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        get_post_api.return_value = None, None, None
        get_ami.return_value = 'ami-test'
        register_agent_to_service.return_value = 'test', 'test'
        get_vpc.return_value = 'test'
        create_instance.return_value = 'test', 'test'
        get_instance.return_value = None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_cloudmanager_connector_aws: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws.NetAppCloudManagerConnectorAWS.delete_instance')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws.NetAppCloudManagerConnectorAWS.get_instance')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.delete')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.delete_occm')
    def test_delete_cloudmanager_connector_aws_pass(self, delete_occm, get_occm_agent_by_id, delete_api, get_instance, delete_instance, get_token):
        set_module_args(self.set_args_delete_cloudmanager_connector_aws())
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        my_instance = {
            'InstanceId': 'instance_id_1'
        }
        get_instance.return_value = my_instance
        get_occm_agent_by_id.return_value = {'agentId': 'test', 'state': 'active'}, None
        delete_api.return_value = None, None, None
        delete_instance.return_value = None
        delete_occm.return_value = None, None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_delete_cloudmanager_connector_aws: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws.NetAppCloudManagerConnectorAWS.delete_instance')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws.NetAppCloudManagerConnectorAWS.get_instance')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.delete')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agents_by_name')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.delete_occm')
    def test_delete_cloudmanager_connector_aws_pass_no_ids(self, delete_occm, get_occm_agents, delete_api, get_instance, delete_instance, get_token):
        args = self.set_args_delete_cloudmanager_connector_aws()
        args.pop('client_id')
        args.pop('instance_id')
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        my_connector_aws = {
            'name': 'Dummyname',
            'client_id': 'test',
            'refresh_token': 'myrefresh_token',
        }
        my_instance = {
            'InstanceId': 'instance_id_1'
        }
        # get_connector_aws.return_value = my_connector_aws
        get_instance.return_value = my_instance
        delete_api.return_value = None, None, None
        delete_instance.return_value = None
        get_occm_agents.return_value = [{'agentId': 'test', 'status': 'active'}], None
        delete_occm.return_value = None, None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print()
        print('Info: test_delete_cloudmanager_connector_aws: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws.NetAppCloudManagerConnectorAWS.delete_instance')
    @patch('ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_connector_aws.NetAppCloudManagerConnectorAWS.get_instance')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.delete')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agents_by_name')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.delete_occm')
    def test_delete_cloudmanager_connector_aws_negative_no_instance(self, delete_occm, get_occm_agents, delete_api, get_instance, delete_instance, get_token):
        args = self.set_args_delete_cloudmanager_connector_aws()
        args.pop('client_id')
        args.pop('instance_id')
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        my_connector_aws = {
            'name': 'Dummyname',
            'client_id': 'test',
            'refresh_token': 'myrefresh_token',
        }
        my_instance = None
        # get_connector_aws.return_value = my_connector_aws
        get_instance.return_value = my_instance
        delete_api.return_value = None, None, None
        delete_instance.return_value = None
        get_occm_agents.return_value = [{'agentId': 'test', 'status': 'active'}], None
        delete_occm.return_value = None, "some error on delete occm"

        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        print()
        print('Info: test_delete_cloudmanager_connector_aws: %s' % repr(exc.value))
        msg = "Error: deleting OCCM agent(s): [(None, 'some error on delete occm')]"
        assert msg in exc.value.args[0]['msg']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_get_instance_empty(self, get_boto3_client, get_token):
        args = self.set_args_delete_cloudmanager_connector_aws()
        args.pop('client_id')
        args.pop('instance_id')
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2()
        my_obj = my_module()
        instance = my_obj.get_instance()
        print('instance', instance)
        assert instance is None

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_get_instance_one(self, get_boto3_client, get_token):
        args = self.set_args_delete_cloudmanager_connector_aws()
        args.pop('client_id')
        args.pop('instance_id')
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'active'}])
        my_obj = my_module()
        instance = my_obj.get_instance()
        print('instance', instance)
        assert instance

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_get_instance_many_terminated(self, get_boto3_client, get_token):
        args = self.set_args_delete_cloudmanager_connector_aws()
        args.pop('client_id')
        args.pop('instance_id')
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'terminated'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        my_obj = my_module()
        instance = my_obj.get_instance()
        print('instance', instance)
        assert instance is None

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_get_instance_many_but_only_one_active(self, get_boto3_client, get_token):
        args = self.set_args_delete_cloudmanager_connector_aws()
        args.pop('client_id')
        args.pop('instance_id')
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'active'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        my_obj = my_module()
        instance = my_obj.get_instance()
        print('instance', instance)
        assert instance

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_get_instance_many_but_only_one_active(self, get_boto3_client, get_token):
        args = self.set_args_delete_cloudmanager_connector_aws()
        args.pop('client_id')
        args.pop('instance_id')
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'active'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'active', 'name': 'xxxx'}])
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.get_instance()
        msg = "Error: found multiple instances for name"
        assert msg in exc.value.args[0]['msg']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_get_instance_exception(self, get_boto3_client, get_token):
        args = self.set_args_delete_cloudmanager_connector_aws()
        args.pop('client_id')
        args.pop('instance_id')
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2(raise_exc=True)
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.get_instance()
        msg = "An error occurred (test_only) when calling the describe_instances operation: forced error in unit testing"
        assert msg in exc.value.args[0]['msg']

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    @patch('boto3.client')
    def test_create_instance(self, get_boto3_client, register, get_token, get_occm_agent_by_id, dont_sleep):
        args = self.set_args_create_cloudmanager_connector_aws()
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'terminated'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        register.return_value = {'clientId': 'xxx', 'clientSecret': 'yyy'}, None, None
        get_occm_agent_by_id.return_value = {'agentId': 'test', 'status': 'active'}, None
        my_obj = my_module()
        instance = my_obj.create_instance()
        print('instance', instance)
        assert instance

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.encode_certificates')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_or_create_account')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    @patch('boto3.client')
    def test_create_instance_no_ami_with_tags(self, get_boto3_client, register, get_token, get_occm_agent_by_id, get_account, encode_cert, dont_sleep):
        ''' additional paths: get_ami, add tags, no public IP, no account id '''
        args = self.set_args_create_cloudmanager_connector_aws()
        args.pop('ami')
        args.pop('account_id')
        args['aws_tag'] = [{'tag_key': 'tkey', 'tag_value': 'tvalue'}]
        args['associate_public_ip_address'] = False
        args['proxy_certificates'] = ['cert1', 'cert2']
        set_module_args(args)
        get_account.return_value = 'account_id', None
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'terminated'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        encode_cert.return_value = 'base64', None
        register.return_value = {'clientId': 'xxx', 'clientSecret': 'yyy'}, None, None
        get_occm_agent_by_id.side_effect = [
            ({'agentId': 'test', 'status': 'pending'}, None),
            ({'agentId': 'test', 'status': 'pending'}, None),
            ({'agentId': 'test', 'status': 'active'}, None)]
        my_obj = my_module()
        instance = my_obj.create_instance()
        print('instance', instance)
        assert instance

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    @patch('boto3.client')
    def test_create_instance_timeout(self, get_boto3_client, register, get_token, get_occm_agent_by_id, dont_sleep):
        ''' additional paths: get_ami, add tags, no public IP'''
        args = self.set_args_create_cloudmanager_connector_aws()
        args.pop('ami')
        args['aws_tag'] = [{'tag_key': 'tkey', 'tag_value': 'tvalue'}]
        args['associate_public_ip_address'] = False
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'terminated'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        register.return_value = {'clientId': 'xxx', 'clientSecret': 'yyy'}, None, None
        get_occm_agent_by_id.return_value = {'agentId': 'test', 'status': 'pending'}, None
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_instance()
        msg = "Error: taking too long for OCCM agent to be active or not properly setup"
        assert msg in exc.value.args[0]['msg']

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    @patch('boto3.client')
    def test_create_instance_error_in_get_agent(self, get_boto3_client, register, get_token, get_occm_agent_by_id, dont_sleep):
        ''' additional paths: get_ami, add tags, no public IP'''
        args = self.set_args_create_cloudmanager_connector_aws()
        args.pop('ami')
        args['aws_tag'] = [{'tag_key': 'tkey', 'tag_value': 'tvalue'}]
        args['associate_public_ip_address'] = False
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'terminated'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        register.return_value = {'clientId': 'xxx', 'clientSecret': 'yyy'}, None, None
        get_occm_agent_by_id.return_value = 'forcing an error', 'intentional error'
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_instance()
        msg = "Error: not able to get occm status: intentional error, forcing an error"
        assert msg in exc.value.args[0]['msg']

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_or_create_account')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_create_instance_error_in_get_account(self, get_boto3_client, get_token, get_account, dont_sleep):
        ''' additional paths: get_ami, add tags, no public IP, no account id '''
        args = self.set_args_create_cloudmanager_connector_aws()
        args.pop('ami')
        args.pop('account_id')
        args['aws_tag'] = [{'tag_key': 'tkey', 'tag_value': 'tvalue'}]
        args['associate_public_ip_address'] = False
        set_module_args(args)
        get_account.return_value = 'forcing an error', 'intentional error'
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'terminated'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_instance()
        msg = "Error: failed to get account: intentional error."
        assert msg in exc.value.args[0]['msg']

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_or_create_account')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    @patch('boto3.client')
    def test_create_instance_error_in_register(self, get_boto3_client, register, get_token, get_account, dont_sleep):
        ''' additional paths: get_ami, add tags, no public IP, no account id '''
        args = self.set_args_create_cloudmanager_connector_aws()
        args.pop('ami')
        args.pop('account_id')
        args['aws_tag'] = [{'tag_key': 'tkey', 'tag_value': 'tvalue'}]
        args['associate_public_ip_address'] = False
        set_module_args(args)
        get_account.return_value = 'account_id', None
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'terminated'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        register.return_value = 'forcing an error', 'intentional error', 'dummy'
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_instance()
        msg = "Error: unexpected response on connector setup: intentional error, forcing an error"
        assert msg in exc.value.args[0]['msg']

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.encode_certificates')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_or_create_account')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    @patch('boto3.client')
    def test_create_instance_error_in_open(self, get_boto3_client, register, get_token, get_account, encode_cert, dont_sleep):
        ''' additional paths: get_ami, add tags, no public IP, no account id '''
        args = self.set_args_create_cloudmanager_connector_aws()
        args.pop('ami')
        args.pop('account_id')
        args['aws_tag'] = [{'tag_key': 'tkey', 'tag_value': 'tvalue'}]
        args['associate_public_ip_address'] = False
        args['proxy_certificates'] = ['cert1', 'cert2']
        set_module_args(args)
        get_account.return_value = 'account_id', None
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'terminated'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        register.return_value = {'clientId': 'xxx', 'clientSecret': 'yyy'}, None, None
        encode_cert.return_value = None, 'intentional error'
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.create_instance()
        msg = "Error: could not open/read file 'cert1' of proxy_certificates: intentional error"
        assert msg in exc.value.args[0]['msg']

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_delete_instance(self, get_boto3_client, get_token, get_occm_agent_by_id, dont_sleep):
        args = self.set_args_delete_cloudmanager_connector_aws()
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'active'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        get_occm_agent_by_id.side_effect = [
            ({'agentId': 'test', 'status': 'active'}, None),
            ({'agentId': 'test', 'status': 'active'}, None),
            ({'agentId': 'test', 'status': 'terminated'}, None)]
        my_obj = my_module()
        error = my_obj.delete_instance()
        assert not error

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.delete_occm_agents')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agents_by_name')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_delete_no_client(self, get_boto3_client, get_token, get_occm_agent_by_id, get_occm_agents_by_name, delete_occm_agents, dont_sleep):
        args = self.set_args_delete_cloudmanager_connector_aws()
        args.pop('client_id')
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'active'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        get_occm_agent_by_id.side_effect = [
            ({'agentId': 'test', 'status': 'active'}, None),
            ({'agentId': 'test', 'status': 'active'}, None),
            ({'agentId': 'test', 'status': 'terminated'}, None)]
        get_occm_agents_by_name.return_value = [], None
        delete_occm_agents.return_value = None
        with pytest.raises(AnsibleExitJson) as exc:
            my_main()
        assert not get_occm_agent_by_id.called

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_delete_instance_timeout(self, get_boto3_client, get_token, get_occm_agent_by_id, dont_sleep):
        args = self.set_args_delete_cloudmanager_connector_aws()
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'active'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        get_occm_agent_by_id.return_value = {'agentId': 'test', 'status': 'active'}, None
        my_obj = my_module()
        error = my_obj.delete_instance()
        assert 'Error: taking too long for instance to finish terminating.' == error

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_delete_instance_error_on_agent(self, get_boto3_client, get_token, get_occm_agent_by_id, dont_sleep):
        args = self.set_args_delete_cloudmanager_connector_aws()
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'active'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        get_occm_agent_by_id.return_value = {'agentId': 'test', 'status': 'active'}, 'intentional error'
        my_obj = my_module()
        error = my_obj.delete_instance()
        assert 'Error: not able to get occm agent status after deleting instance: intentional error,' in error

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_delete_instance_client_id_not_found_403(self, get_boto3_client, get_token, get_occm_agent_by_id, dont_sleep):
        args = self.set_args_delete_cloudmanager_connector_aws()
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'active'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        get_occm_agent_by_id.return_value = 'Action not allowed for user', '403'
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        msg = "Error: not able to get occm agent status after deleting instance: 403,"
        assert msg in exc.value.args[0]['msg']
        print(exc.value.args[0])

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_delete_instance_client_id_not_found_other(self, get_boto3_client, get_token, get_occm_agent_by_id, dont_sleep):
        args = self.set_args_delete_cloudmanager_connector_aws()
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'active'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        get_occm_agent_by_id.return_value = 'Other error', '404'
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        msg = "Error: getting OCCM agents: 404,"
        assert msg in exc.value.args[0]['msg']

    @patch('time.sleep')
    # @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agent_by_id')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_delete_instance_account_id_not_found(self, get_boto3_client, get_token, dont_sleep):
        args = self.set_args_delete_cloudmanager_connector_aws()
        args.pop('account_id')
        args.pop('client_id')
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'active'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        # get_occm_agent_by_id.return_value = 'Other error', '404'
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        # msg = "Error: getting OCCM agents: 404,"
        assert exc.value.args[0]['account_id'] is None
        assert exc.value.args[0]['client_id'] is None

    @patch('time.sleep')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_occm_agents_by_name')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('boto3.client')
    def test_modify_instance(self, get_boto3_client, get_token, get_occm_agents_by_name, dont_sleep):
        args = self.set_args_create_cloudmanager_connector_aws()
        args['instance_type'] = 't3.large'
        set_module_args(args)
        get_token.return_value = 'test', 'test'
        get_boto3_client.return_value = EC2([{'state': 'active'},
                                             {'state': 'terminated', 'reservation': '2'},
                                             {'state': 'terminated', 'name': 'xxxx'}])
        get_occm_agents_by_name.return_value = [{'agentId': 'test', 'status': 'active'}], None
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        msg = "Note: modifying an existing connector is not supported at this time."
        assert msg == exc.value.args[0]['modify']


class EC2:
    def __init__(self, get_instances=None, create_instance=True, raise_exc=False):
        ''' list of instances as dictionaries:
            name, state are optional, and used to build an instance
            reservation is optional and defaults to 'default'
        '''
        self.get_instances = get_instances if get_instances is not None else []
        self.create_instance = create_instance if create_instance is not None else []
        self.raise_exc = raise_exc

    def describe_instances(self, Filters=None, InstanceIds=None):
        ''' return a list of reservations, each reservation is a list of instances
        '''
        if self.raise_exc and HAS_BOTOCORE:
            raise ClientError({'Error': {'Message': 'forced error in unit testing', 'Code': 'test_only'}}, 'describe_instances')
        print('ec2', Filters)
        print('ec2', InstanceIds)
        return self._build_reservations()

    def describe_images(self, Filters=None, Owners=None):
        ''' AMI '''
        return {'Images': [{'CreationDate': 'yyyyy', 'ImageId': 'image_id'},
                           {'CreationDate': 'xxxxx', 'ImageId': 'image_id'},
                           {'CreationDate': 'zzzzz', 'ImageId': 'image_id'}]}

    def describe_subnets(self, SubnetIds=None):
        ''' subnets '''
        return {'Subnets': [{'VpcId': 'vpc_id'}]}

    def run_instances(self, **kwargs):
        ''' create and start an instance'''
        if self.create_instance:
            return {'Instances': [{'InstanceId': 'instance_id'}]}
        return {'Instances': []}

    def terminate_instances(self, **kwargs):
        ''' terminate an instance'''
        return

    def _build_reservations(self):
        ''' return a list of reservations, each reservation is a list of instances
        '''
        reservations = {}
        for instance in self.get_instances:
            reservation = instance.get('reservation', 'default')
            if reservation not in reservations:
                reservations[reservation] = []
            # provide default values for name or state if one is present
            name, state = None, None
            if 'name' in instance:
                name = instance['name']
                state = instance.get('state', 'active')
            elif 'state' in instance:
                name = instance.get('name', 'd_name')
                state = instance['state']
            instance_id = instance.get('instance_id', '12345')
            instance_type = instance.get('instance_type', 't3.xlarge')
            if name:
                reservations[reservation].append({'Name': name, 'State': {'Name': state}, 'InstanceId': instance_id, 'InstanceType': instance_type})
        return {
            'Reservations': [
                {'Instances': instances} for instances in reservations.values()
            ]
        }
