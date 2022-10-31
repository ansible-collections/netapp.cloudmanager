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
from ansible_collections.netapp.cloudmanager.tests.unit.compat.mock import patch, Mock
import ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.cloudmanager.plugins.modules.na_cloudmanager_cvo_azure \
    import NetAppCloudManagerCVOAZURE as my_module

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


class MockCMConnection():
    ''' Mock response of http connections '''

    def __init__(self, kind=None, parm1=None):
        self.type = kind
        self.parm1 = parm1
        # self.token_type, self.token = self.get_token()


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
            'client_id': 'test',
            'location': 'westus',
            'use_latest_version': False,
            'ontap_version': 'ONTAP-9.10.0.T1.azure',
            'vnet_id': 'vpc-test',
            'resource_group': 'test',
            'subnet_id': 'subnet-test',
            'subscription_id': 'test',
            'cidr': '10.0.0.0/24',
            'svm_password': 'password',
            'license_type': 'azure-cot-standard-paygo',
            'instance_type': 'Standard_DS4_v2',
            'refresh_token': 'myrefresh_token',
            'is_ha': False
        })

    def set_args_create_cloudmanager_cvo_azure(self):
        return dict({
            'state': 'present',
            'name': 'Dummyname',
            'client_id': 'test',
            'location': 'westus',
            'vnet_id': 'vpc-test',
            'resource_group': 'test',
            'subscription_id': 'test',
            'cidr': '10.0.0.0/24',
            'subnet_id': 'subnet-test',
            'svm_password': 'password',
            'refresh_token': 'myrefresh_token',
            'is_ha': False
        })

    def set_args_delete_cloudmanager_cvo_azure(self):
        return dict({
            'state': 'absent',
            'name': 'Dummyname',
            'client_id': 'test',
            'location': 'westus',
            'vnet_id': 'vpc-test',
            'resource_group': 'test',
            'subscription_id': 'test',
            'cidr': '10.0.0.0/24',
            'subnet_id': 'subnet-test',
            'svm_password': 'password',
            'refresh_token': 'myrefresh_token',
            'is_ha': False
        })

    def set_args_create_bynode_cloudmanager_cvo_azure(self):
        return dict({
            'state': 'present',
            'name': 'Dummyname',
            'client_id': 'test',
            'location': 'westus',
            'vnet_id': 'vpc-test',
            'resource_group': 'test',
            'subscription_id': 'test',
            'cidr': '10.0.0.0/24',
            'subnet_id': 'subnet-test',
            'svm_password': 'password',
            'refresh_token': 'myrefresh_token',
            'license_type': 'azure-cot-premium-byol',
            'serial_number': '12345678',
            'is_ha': False
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
            self.rest_api = MockCMConnection()
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
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.wait_on_completion')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_tenant')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_nss')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_working_environment_details_by_name')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    def test_create_cloudmanager_cvo_azure_pass(self, get_post_api, get_working_environment_details_by_name, get_nss,
                                                get_tenant, wait_on_completion, get_token):
        set_module_args(self.set_args_create_cloudmanager_cvo_azure())
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        response = {'publicId': 'abcdefg12345'}
        get_post_api.return_value = response, None, None
        get_working_environment_details_by_name.return_value = None, None
        get_nss.return_value = 'nss-test', None
        get_tenant.return_value = 'test', None
        wait_on_completion.return_value = None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_cloudmanager_cvo_azure_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.wait_on_completion')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_tenant')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_nss')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_working_environment_details_by_name')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    def test_create_cloudmanager_cvo_azure_capacity_license_pass(self, get_post_api,
                                                                 get_working_environment_details_by_name, get_nss,
                                                                 get_tenant, wait_on_completion, get_token):
        data = self.set_args_create_cloudmanager_cvo_azure()
        data['license_type'] = 'capacity-paygo'
        data['capacity_package_name'] = 'Essential'
        set_module_args(data)
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        response = {'publicId': 'abcdefg12345'}
        get_post_api.return_value = response, None, None
        get_working_environment_details_by_name.return_value = None, None
        get_nss.return_value = 'nss-test', None
        get_tenant.return_value = 'test', None
        wait_on_completion.return_value = None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_cloudmanager_cvo_azure_capacity_license_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.wait_on_completion')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_tenant')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_nss')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_working_environment_details_by_name')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    def test_create_cloudmanager_cvo_azure_ha_capacity_license_pass(self, get_post_api,
                                                                    get_working_environment_details_by_name, get_nss,
                                                                    get_tenant, wait_on_completion, get_token):
        data = self.set_args_create_cloudmanager_cvo_azure()
        data['is_ha'] = True
        data['license_type'] = 'ha-capacity-paygo'
        data['capacity_package_name'] = 'Professional'
        set_module_args(data)
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        response = {'publicId': 'abcdefg12345'}
        get_post_api.return_value = response, None, None
        get_working_environment_details_by_name.return_value = None, None
        get_nss.return_value = 'nss-test', None
        get_tenant.return_value = 'test', None
        wait_on_completion.return_value = None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_cloudmanager_cvo_azure_ha_capacity_license_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.wait_on_completion')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_tenant')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_nss')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_working_environment_details_by_name')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    def test_create_cloudmanager_cvo_azure_nodebase_license_pass(self, get_post_api,
                                                                 get_working_environment_details_by_name, get_nss,
                                                                 get_tenant, wait_on_completion, get_token):
        data = self.set_args_create_bynode_cloudmanager_cvo_azure()
        set_module_args(data)
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        response = {'publicId': 'abcdefg12345'}
        get_post_api.return_value = response, None, None
        get_working_environment_details_by_name.return_value = None, None
        get_nss.return_value = 'nss-test', None
        get_tenant.return_value = 'test', None
        wait_on_completion.return_value = None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_cloudmanager_cvo_azure_nodebase_license_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.wait_on_completion')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_tenant')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_nss')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_working_environment_details_by_name')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    def test_create_cloudmanager_cvo_azure_ha_nodebase_license_pass(self, get_post_api,
                                                                    get_working_environment_details_by_name, get_nss,
                                                                    get_tenant, wait_on_completion, get_token):
        data = self.set_args_create_bynode_cloudmanager_cvo_azure()
        data['is_ha'] = True
        data['license_type'] = 'azure-ha-cot-premium-byol'
        data['platform_serial_number_node1'] = '12345678'
        data['platform_serial_number_node2'] = '23456789'
        set_module_args(data)
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        response = {'publicId': 'abcdefg12345'}
        get_post_api.return_value = response, None, None
        get_working_environment_details_by_name.return_value = None, None
        get_nss.return_value = 'nss-test', None
        get_tenant.return_value = 'test', None
        wait_on_completion.return_value = None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_cloudmanager_cvo_azure_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.wait_on_completion')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_tenant')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_nss')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_working_environment_details_by_name')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.post')
    def test_create_cloudmanager_cvo_azure_ha_pass(self, get_post_api, get_working_environment_details_by_name, get_nss,
                                                   get_tenant, wait_on_completion, get_token):
        data = self.set_args_create_cloudmanager_cvo_azure()
        data['is_ha'] = True
        data['license_type'] = 'ha-capacity-paygo'
        data['capacity_package_name'] = 'Essential'
        set_module_args(data)
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        response = {'publicId': 'abcdefg12345'}
        get_post_api.return_value = response, None, None
        get_working_environment_details_by_name.return_value = None, None
        get_nss.return_value = 'nss-test', None
        get_tenant.return_value = 'test', None
        wait_on_completion.return_value = None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_create_cloudmanager_cvo_azure_ha_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.wait_on_completion')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_working_environment_details_by_name')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.delete')
    def test_delete_cloudmanager_cvo_azure_pass(self, get_delete_api, get_working_environment_details_by_name,
                                                wait_on_completion, get_token):
        set_module_args(self.set_args_delete_cloudmanager_cvo_azure())
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        my_cvo = {
            'name': 'Dummyname',
            'publicId': 'test'}
        get_working_environment_details_by_name.return_value = my_cvo, None
        get_delete_api.return_value = None, None, None
        wait_on_completion.return_value = None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_delete_cloudmanager_cvo_azure_pass: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp.CloudManagerRestAPI.get_token')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.update_writing_speed_state')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.update_instance_license_type')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.update_tier_level')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.update_cvo_tags')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.update_svm_password')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.upgrade_ontap_image')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_working_environment_details')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_working_environment_property')
    @patch('ansible_collections.netapp.cloudmanager.plugins.module_utils.netapp_module.NetAppModule.get_working_environment_details_by_name')
    def test_change_cloudmanager_cvo_azure(self, get_cvo, get_property, get_details, upgrade_ontap_image, update_svm_password, update_cvo_tags,
                                           update_tier_level, update_instance_license_type, update_writing_speed_state, get_token):
        data = self.set_default_args_pass_check()
        data['svm_password'] = 'newpassword'
        data['update_svm_password'] = True
        data['ontap_version'] = 'ONTAP-9.10.1P3.T1.azure'
        data['upgrade_ontap_version'] = True
        data['instance_type'] = 'Standard_DS13_v2'
        set_module_args(data)

        modify = ['svm_password', 'azure_tag', 'tier_level', 'ontap_version', 'instance_type', 'license_type']

        my_cvo = {
            'name': 'TestA',
            'publicId': 'test',
            'svm_password': 'password',
            'isHA': False,
            'azure_tag': [{'tag_key': 'keya', 'tag_value': 'valuea'}, {'tag_key': 'keyb', 'tag_value': 'valueb'}],
        }
        get_cvo.return_value = my_cvo, None

        cvo_property = {'name': 'TestA',
                        'publicId': 'test',
                        'status': {'status': 'ON'},
                        'ontapClusterProperties': {
                            'capacityTierInfo': {'tierLevel': 'normal'},
                            'licensePackageName': 'Professional',
                            'licenseType': {'capacityLimit': {'size': 2000.0, 'unit': 'TB'},
                                            'name': 'Cloud Volumes ONTAP Capacity Based Charging'},
                            'ontapVersion': '9.10.0.T1.azure',
                            'upgradeVersions': [{'autoUpdateAllowed': False,
                                                 'imageVersion': 'ONTAP-9.10.1P3',
                                                 'lastModified': 1634467078000}],
                            'writingSpeedState': 'NORMAL'},
                        'providerProperties': {
                            'cloudProviderAccountId': 'CloudProviderAccount-abcdwxyz',
                            'regionName': 'westus',
                            'instanceType': 'Standard_DS4_v2',
                            'resourceGroup': {
                                'name': 'TestA-rg',
                                'location': 'westus',
                                'tags': {
                                    'DeployedByOccm': 'true'
                                }
                            },
                            'vnetCidr': '10.0.0.0/24',
                            'tags': {
                                'DeployedByOccm': 'true'
                            }},
                        'tenantId': 'Tenant-abCdEfg1',
                        'workingEnvironmentTyp': 'VSA'
                        }
        get_property.return_value = cvo_property, None
        cvo_details = {'cloudProviderName': 'Azure',
                       'isHA': False,
                       'name': 'TestA',
                       'ontapClusterProperties': None,
                       'publicId': 'test',
                       'status': {'status': 'ON'},
                       'userTags': {'DeployedByOccm': 'true', 'key1': 'value1'},
                       'workingEnvironmentType': 'VSA'}
        get_details.return_value = cvo_details, None
        get_token.return_value = 'test', 'test'
        my_obj = my_module()

        for item in modify:
            if item == 'svm_password':
                update_svm_password.return_value = True, None
            elif item == 'azure_tag':
                update_cvo_tags.return_value = True, None
            elif item == 'tier_level':
                update_tier_level.return_value = True, None
            elif item == 'ontap_version':
                upgrade_ontap_image.return_value = True, None
            elif item == 'writing_speed_state':
                update_writing_speed_state.return_value = True, None
            elif item == 'instance_type':
                update_instance_license_type.return_value = True, None

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_change_cloudmanager_cvo_azure: %s' % repr(exc.value))
        assert exc.value.args[0]['changed']
