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

''' Support class for NetApp ansible modules '''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from copy import deepcopy
import json
import re
import base64


def cmp(a, b):
    '''
    Python 3 does not have a cmp function, this will do the cmp.
    :param a: first object to check
    :param b: second object to check
    :return:
    '''
    # convert to lower case for string comparison.
    if a is None:
        return -1
    if isinstance(a, str) and isinstance(b, str):
        a = a.lower()
        b = b.lower()
    # if list has string element, convert string to lower case.
    if isinstance(a, list) and isinstance(b, list):
        a = [x.lower() if isinstance(x, str) else x for x in a]
        b = [x.lower() if isinstance(x, str) else x for x in b]
        a.sort()
        b.sort()
    return (a > b) - (a < b)


class NetAppModule(object):
    '''
    Common class for NetApp modules
    set of support functions to derive actions based
    on the current state of the system, and a desired state
    '''

    def __init__(self):
        self.log = list()
        self.changed = False
        self.parameters = {'name': 'not intialized'}

    def set_parameters(self, ansible_params):
        self.parameters = dict()
        for param in ansible_params:
            if ansible_params[param] is not None:
                self.parameters[param] = ansible_params[param]
        return self.parameters

    def get_cd_action(self, current, desired):
        ''' takes a desired state and a current state, and return an action:
            create, delete, None
            eg:
            is_present = 'absent'
            some_object = self.get_object(source)
            if some_object is not None:
                is_present = 'present'
            action = cd_action(current=is_present, desired = self.desired.state())
        '''
        if 'state' in desired:
            desired_state = desired['state']
        else:
            desired_state = 'present'

        if current is None and desired_state == 'absent':
            return None
        if current is not None and desired_state == 'present':
            return None
        # change in state
        self.changed = True
        if current is not None:
            return 'delete'
        return 'create'

    def compare_and_update_values(self, current, desired, keys_to_compare):
        updated_values = dict()
        is_changed = False
        for key in keys_to_compare:
            if key in current:
                if key in desired and desired[key] is not None:
                    if current[key] != desired[key]:
                        updated_values[key] = desired[key]
                        is_changed = True
                    else:
                        updated_values[key] = current[key]
                else:
                    updated_values[key] = current[key]

        return updated_values, is_changed

    def get_working_environments_info(self, rest_api, headers):
        '''
        Get all working environments info
        '''
        api = "/occm/api/working-environments"
        response, error, dummy = rest_api.get(api, None, header=headers)
        if error is not None:
            return response, error
        else:
            return response, None

    def look_up_working_environment_by_name_in_list(self, we_list, name='working_environment_name'):
        '''
        Look up working environment by the name in working environment list
        '''
        for we in we_list:
            if we['name'] == name:
                return we, None
        return None, "Working environment not found"

    def get_working_environment_details_by_name(self, rest_api, headers, name='working_environment_name', provider=None):
        '''
        Use working environment name to get working environment details including:
        name: working environment name,
        publicID: working environment ID
        cloudProviderName,
        isHA,
        svmName
        '''
        # check the working environment exist or not
        api = "/occm/api/working-environments/exists/" + name
        response, error, dummy = rest_api.get(api, None, header=headers)
        if error is not None:
            return None, error

        # get working environment lists
        api = "/occm/api/working-environments"
        response, error, dummy = rest_api.get(api, None, header=headers)
        if error is not None:
            return None, error
        # look up the working environment in the working environment lists
        if provider is None or provider == 'onPrem':
            working_environment_details, error = self.look_up_working_environment_by_name_in_list(response['onPremWorkingEnvironments'], name)
            if error is None:
                return working_environment_details, None
        if provider is None or provider == 'gcp':
            working_environment_details, error = self.look_up_working_environment_by_name_in_list(response['gcpVsaWorkingEnvironments'], name)
            if error is None:
                return working_environment_details, None
        if provider is None or provider == 'azure':
            working_environment_details, error = self.look_up_working_environment_by_name_in_list(response['azureVsaWorkingEnvironments'], name)
            if error is None:
                return working_environment_details, None
        if provider is None or provider == 'aws':
            working_environment_details, error = self.look_up_working_environment_by_name_in_list(response['vsaWorkingEnvironments'], name)
            if error is None:
                return working_environment_details, None
        return None, "Working environment not found"

    def get_working_environment_details(self, rest_api, headers):
        '''
        Use working environment id to get working environment details including:
        name: working environment name,
        publicID: working environment ID
        cloudProviderName,
        isHA,
        svmName
        '''
        api = "/occm/api/working-environments/"
        api += self.parameters['working_environment_id']
        response, error, dummy = rest_api.get(api, None, header=headers)
        if error:
            return None, error
        return response, None

    def get_working_environment_detail_for_snapmirror(self, rest_api, headers):

        if self.parameters.get('source_working_environment_id'):
            api = '/occm/api/working-environments/'
            api += self.parameters['source_working_environment_id']
            source_working_env_detail, error, dummy = rest_api.get(api, None, header=headers)
            if error:
                return None, None, error
        elif self.parameters.get('source_working_environment_name'):
            source_working_env_detail, error = self.get_working_environment_details_by_name(rest_api, headers, 'source_working_environment_name')
            if error:
                return None, None, error
        else:
            return None, None, "Cannot find working environment by source_working_environment_id or source_working_environment_name"

        if self.parameters.get('destination_working_environment_id'):
            api = '/occm/api/working-environments/'
            api += self.parameters['destination_working_environment_id']
            dest_working_env_detail, error, dummy = rest_api.get(api, None, header=headers)
            if error:
                return None, None, error
        elif self.parameters.get('destination_working_environment_name'):
            dest_working_env_detail, error = self.get_working_environment_details_by_name(rest_api, headers, 'destination_working_environment_name')
            if error:
                return None, None, error
        else:
            return None, None, "Cannot find working environment by destination_working_environment_id or destination_working_environment_name"

        return source_working_env_detail, dest_working_env_detail, None

    def create_account(self, host, rest_api):
        """
        Create Account
        :return: Account ID
        """
        headers = {
            "X-User-Token": rest_api.token_type + " " + rest_api.token,
        }

        url = host + '/tenancy/account/MyAccount'
        account_res, error, dummy = rest_api.post(url, header=headers)
        if error is not None:
            account_id = None
        else:
            account_id = account_res['accountPublicId']

        return account_id, error

    def get_account(self, host, rest_api):
        """
        Get Account
        :return: Account ID
        """
        headers = {
            "X-User-Token": rest_api.token_type + " " + rest_api.token,
        }

        url = host + '/tenancy/account'
        account_res, error, dummy = rest_api.get(url, header=headers)
        if error is not None:
            return None, error
        if len(account_res) == 0:
            account_id, error = self.create_account(host, rest_api)
            if error is not None:
                return None, error
            return account_id, None

        return account_res[0]['accountPublicId'], None

    def get_accounts_info(self, rest_api, headers):
        '''
        Get all accounts info
        '''
        api = "/occm/api/accounts"
        response, error, dummy = rest_api.get(api, None, header=headers)
        if error is not None:
            return None, error
        else:
            return response, None

    def set_api_root_path(self, working_environment_details, rest_api):
        '''
        set API url root path based on the working environment provider
        '''
        provider = working_environment_details['cloudProviderName']
        is_ha = working_environment_details['isHA']
        api_root_path = None
        if provider != "Amazon":
            if is_ha:
                api_root_path = "/occm/api/" + provider.lower() + "/ha"
            else:
                api_root_path = "/occm/api/" + provider.lower() + "/vsa"
        else:
            if is_ha:
                api_root_path = "/occm/api/aws/ha"
            else:
                api_root_path = "/occm/api/vsa"
        rest_api.api_root_path = api_root_path

    def have_required_parameters(self, action):
        '''
        Check if all the required parameters in self.params are available or not besides the mandatory parameters
        '''
        actions = {'create_aggregate': ['number_of_disks', 'disk_size_size', 'disk_size_unit', 'working_environment_id'],
                   'update_aggregate': ['number_of_disks', 'disk_size_size', 'disk_size_unit', 'working_environment_id'],
                   'delete_aggregate': ['working_environment_id'],
                   }
        missed_params = []
        for parameter in actions[action]:
            if parameter not in self.parameters:
                missed_params.append(parameter)

        if not missed_params:
            return True, None
        else:
            return False, missed_params

    def get_modified_attributes(self, current, desired, get_list_diff=False):
        ''' takes two dicts of attributes and return a dict of attributes that are
            not in the current state
            It is expected that all attributes of interest are listed in current and
            desired.
            :param: current: current attributes in ONTAP
            :param: desired: attributes from playbook
            :param: get_list_diff: specifies whether to have a diff of desired list w.r.t current list for an attribute
            :return: dict of attributes to be modified
            :rtype: dict

            NOTE: depending on the attribute, the caller may need to do a modify or a
            different operation (eg move volume if the modified attribute is an
            aggregate name)
        '''
        # if the object does not exist,  we can't modify it
        modified = dict()
        if current is None:
            return modified

        # error out if keys do not match
        # self.check_keys(current, desired)

        # collect changed attributes
        for key, value in current.items():
            if key in desired and desired[key] is not None:
                if isinstance(value, list):
                    modified_list = self.compare_lists(value, desired[key], get_list_diff)  # get modified list from current and desired
                    if modified_list is not None:
                        modified[key] = modified_list
                elif isinstance(value, dict):
                    modified_dict = self.get_modified_attributes(value, desired[key])
                    if modified_dict:
                        modified[key] = modified_dict
                else:
                    try:
                        result = cmp(value, desired[key])
                    except TypeError as exc:
                        raise TypeError("%s, key: %s, value: %s, desired: %s" % (repr(exc), key, repr(value), repr(desired[key])))
                    else:
                        if result != 0:
                            modified[key] = desired[key]
        if modified:
            self.changed = True
        return modified

    @staticmethod
    def compare_lists(current, desired, get_list_diff):
        ''' compares two lists and return a list of elements that are either the desired elements or elements that are
            modified from the current state depending on the get_list_diff flag
            :param: current: current item attribute in ONTAP
            :param: desired: attributes from playbook
            :param: get_list_diff: specifies whether to have a diff of desired list w.r.t current list for an attribute
            :return: list of attributes to be modified
            :rtype: list
        '''
        current_copy = deepcopy(current)
        desired_copy = deepcopy(desired)

        # get what in desired and not in current
        desired_diff_list = list()
        for item in desired:
            if item in current_copy:
                current_copy.remove(item)
            else:
                desired_diff_list.append(item)

        # get what in current but not in desired
        current_diff_list = list()
        for item in current:
            if item in desired_copy:
                desired_copy.remove(item)
            else:
                current_diff_list.append(item)

        if desired_diff_list or current_diff_list:
            # there are changes
            if get_list_diff:
                return desired_diff_list
            else:
                return desired
        else:
            return None

    @staticmethod
    def convert_module_args_to_api(parameters, exclusion=None):
        '''
        Convert a list of string module args to API option format.
        For example, convert test_option to testOption.
        :param parameters: dict of parameters to be converted.
        :param exclusion: list of parameters to be ignored.
        :return: dict of key value pairs.
        '''
        exclude_list = ['api_url', 'token_type', 'refresh_token', 'sa_secret_key', 'sa_client_id']
        if exclusion is not None:
            exclude_list += exclusion
        api_keys = dict()
        for k, v in parameters.items():
            if k not in exclude_list:
                words = k.split("_")
                api_key = ""
                for word in words:
                    if len(api_key) > 0:
                        word = word.title()
                    api_key = api_key + word
                api_keys[api_key] = v
        return api_keys

    @staticmethod
    def convert_data_to_tabbed_jsonstring(data):
        '''
        Convert a dictionary data to json format string
        '''
        dump = json.dumps(data, indent=2, separators=(',', ': '))
        tabbed = re.sub('\n +', lambda match: '\n' + '\t' * int(len(match.group().strip('\n')) / 2), dump)
        return tabbed

    @staticmethod
    def encode_certificates(certificate_file):
        '''
        Read certificate file and encode it
        '''
        try:
            fh = open(certificate_file, mode='rb')
        except (OSError, IOError) as error:
            return None, error
        with fh:
            cert = fh.read()
            if cert is None:
                return None, "Error: file is empty"
            return base64.b64encode(cert), None

    @staticmethod
    def check_occm_status(host, rest_api, client_id):
        """
        Check OCCM status
        :return: status
        """

        get_occum_url = host + "/agents-mgmt/agent/" + rest_api.format_cliend_id(client_id)
        headers = {
            "X-User-Token": rest_api.token_type + " " + rest_api.token,
        }
        occm_status, error, dummy = rest_api.get(get_occum_url, header=headers)
        return occm_status, error

    def register_agent_to_service(self, host, rest_api, provider, vpc):
        '''
        register agent to service
        '''
        api_url = host + '/agents-mgmt/connector-setup'

        headers = {
            "X-User-Token": rest_api.token_type + " " + rest_api.token,
        }
        body = {
            "accountId": self.parameters['account_id'],
            "name": self.parameters['name'],
            "company": self.parameters['company'],
            "placement": {
                "provider": provider,
                "region": self.parameters['region'],
                "network": vpc,
                "subnet": self.parameters['subnet_id'],
            },
            "extra": {
                "proxy": {
                    "proxyUrl": self.parameters.get('proxy_url'),
                    "proxyUserName": self.parameters.get('proxy_user_name'),
                    "proxyPassword": self.parameters.get('proxy_password'),
                }
            }
        }

        if provider == "AWS":
            body['placement']['network'] = vpc

        response, error, dummy = rest_api.post(api_url, body, header=headers)
        return response, error

    def delete_occm(self, host, rest_api, client_id):
        '''
        delete occm
        '''
        api_url = host + '/agents-mgmt/agent/' + rest_api.format_cliend_id(client_id)
        headers = {
            "X-User-Token": rest_api.token_type + " " + rest_api.token,
            "X-Tenancy-Account-Id": self.parameters['account_id'],
        }

        occm_status, error, dummy = rest_api.delete(api_url, None, header=headers)
        return occm_status, error

    @staticmethod
    def call_parameters():
        return """
        {
            "location": {
                "value": "string"
            },
            "virtualMachineName": {
                "value": "string"
            },
            "virtualMachineSize": {
                "value": "string"
            },
            "networkSecurityGroupName": {
                "value": "string"
            },
            "adminUsername": {
                "value": "string"
            },
            "virtualNetworkId": {
                "value": "string"
            },
            "adminPassword": {
                "value": "string"
            },
            "subnetId": {
                "value": "string"
            },
            "customData": {
            "value": "string"
            },
            "environment": {
                "value": "prod"
            }
        }
        """

    @staticmethod
    def call_template():
        return """
        {
        "$schema": "http://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "location": {
                "type": "string",
                "defaultValue": "eastus"
            },
            "virtualMachineName": {
                "type": "string"
            },
            "virtualMachineSize":{
                "type": "string"
            },
            "adminUsername": {
                "type": "string"
            },
            "virtualNetworkId": {
                "type": "string"
            },
            "networkSecurityGroupName": {
                "type": "string"
            },
            "adminPassword": {
                "type": "securestring"
            },
            "subnetId": {
                "type": "string"
            },
            "customData": {
              "type": "string"
            },
            "environment": {
              "type": "string",
              "defaultValue": "prod"
            }
        },
        "variables": {
            "vnetId": "[parameters('virtualNetworkId')]",
            "subnetRef": "[parameters('subnetId')]",
            "networkInterfaceName": "[concat(parameters('virtualMachineName'),'-nic')]",
            "diagnosticsStorageAccountName": "[concat(toLower(parameters('virtualMachineName')),'sa')]",
            "diagnosticsStorageAccountId": "[concat('Microsoft.Storage/storageAccounts/', variables('diagnosticsStorageAccountName'))]",
            "diagnosticsStorageAccountType": "Standard_LRS",
            "publicIpAddressName": "[concat(parameters('virtualMachineName'),'-ip')]",
            "publicIpAddressType": "Dynamic",
            "publicIpAddressSku": "Basic",
            "msiExtensionName": "ManagedIdentityExtensionForLinux",
            "occmOffer": "[if(equals(parameters('environment'), 'stage'), 'netapp-oncommand-cloud-manager-staging-preview', 'netapp-oncommand-cloud-manager')]"
        },
        "resources": [
            {
                "name": "[parameters('virtualMachineName')]",
                "type": "Microsoft.Compute/virtualMachines",
                "apiVersion": "2018-04-01",
                "location": "[parameters('location')]",
                "dependsOn": [
                    "[concat('Microsoft.Network/networkInterfaces/', variables('networkInterfaceName'))]",
                    "[concat('Microsoft.Storage/storageAccounts/', variables('diagnosticsStorageAccountName'))]"
                ],
                "properties": {
                    "osProfile": {
                        "computerName": "[parameters('virtualMachineName')]",
                        "adminUsername": "[parameters('adminUsername')]",
                        "adminPassword": "[parameters('adminPassword')]",
                        "customData": "[base64(parameters('customData'))]"
                    },
                    "hardwareProfile": {
                        "vmSize": "[parameters('virtualMachineSize')]"
                    },
                    "storageProfile": {
                        "imageReference": {
                            "publisher": "netapp",
                            "offer": "[variables('occmOffer')]",
                            "sku": "occm-byol",
                            "version": "latest"
                        },
                        "osDisk": {
                            "createOption": "fromImage",
                            "managedDisk": {
                                "storageAccountType": "Premium_LRS"
                            }
                        },
                        "dataDisks": []
                    },
                    "networkProfile": {
                        "networkInterfaces": [
                            {
                                "id": "[resourceId('Microsoft.Network/networkInterfaces', variables('networkInterfaceName'))]"
                            }
                        ]
                    },
                    "diagnosticsProfile": {
                      "bootDiagnostics": {
                        "enabled": true,
                        "storageUri":
                          "[concat('https://', variables('diagnosticsStorageAccountName'), '.blob.core.windows.net/')]"
                      }
                    }
                },
                "plan": {
                    "name": "occm-byol",
                    "publisher": "netapp",
                    "product": "[variables('occmOffer')]"
                },
                "identity": {
                    "type": "systemAssigned"
                }
            },
            {
                "apiVersion": "2017-12-01",
                "type": "Microsoft.Compute/virtualMachines/extensions",
                "name": "[concat(parameters('virtualMachineName'),'/', variables('msiExtensionName'))]",
                "location": "[parameters('location')]",
                "dependsOn": [
                    "[concat('Microsoft.Compute/virtualMachines/', parameters('virtualMachineName'))]"
                ],
                "properties": {
                    "publisher": "Microsoft.ManagedIdentity",
                    "type": "[variables('msiExtensionName')]",
                    "typeHandlerVersion": "1.0",
                    "autoUpgradeMinorVersion": true,
                    "settings": {
                        "port": 50342
                    }
                }
            },
            {
                "name": "[variables('diagnosticsStorageAccountName')]",
                "type": "Microsoft.Storage/storageAccounts",
                "apiVersion": "2015-06-15",
                "location": "[parameters('location')]",
                "properties": {
                  "accountType": "[variables('diagnosticsStorageAccountType')]"
                }
            },
            {
                "name": "[variables('networkInterfaceName')]",
                "type": "Microsoft.Network/networkInterfaces",
                "apiVersion": "2018-04-01",
                "location": "[parameters('location')]",
                "dependsOn": [
                    "[concat('Microsoft.Network/publicIpAddresses/', variables('publicIpAddressName'))]"
                ],
                "properties": {
                    "ipConfigurations": [
                        {
                            "name": "ipconfig1",
                            "properties": {
                                "subnet": {
                                    "id": "[variables('subnetRef')]"
                                },
                                "privateIPAllocationMethod": "Dynamic",
                                "publicIpAddress": {
                                    "id": "[resourceId(resourceGroup().name,'Microsoft.Network/publicIpAddresses', variables('publicIpAddressName'))]"
                                }
                            }
                        }
                    ],
                    "networkSecurityGroup": {
                        "id": "[parameters('networkSecurityGroupName')]"
                    }
                }
            },
            {
                "name": "[variables('publicIpAddressName')]",
                "type": "Microsoft.Network/publicIpAddresses",
                "apiVersion": "2017-08-01",
                "location": "[parameters('location')]",
                "properties": {
                    "publicIpAllocationMethod": "[variables('publicIpAddressType')]"
                },
                "sku": {
                    "name": "[variables('publicIpAddressSku')]"
                }
            }
        ],
        "outputs": {
            "publicIpAddressName": {
                "type": "string",
                "value": "[variables('publicIpAddressName')]"
            }
        }
    }
    """

    def get_tenant(self, rest_api, headers):
        """
        Get workspace ID (tenant)
        """
        api_url = '/occm/api/tenants'
        response, error, dummy = rest_api.get(api_url, header=headers)
        if error is not None:
            return None, 'Error: unexpected response on getting tenant for cvo: %s, %s' % (str(error), str(response))

        return response[0]['publicId'], None

    def get_nss(self, rest_api, headers):
        """
        Get nss account
        """
        api_url = '/occm/api/accounts'
        response, error, dummy = rest_api.get(api_url, header=headers)
        if error is not None:
            return None, 'Error: unexpected response on getting nss for cvo: %s, %s' % (str(error), str(response))

        if len(response['nssAccounts']) == 0:
            return None, "Error: could not find any NSS account"

        return response['nssAccounts'][0]['publicId'], None

    def get_working_environment_property(self, rest_api, headers):
        # GET /vsa/working-environments/{workingEnvironmentId}?fields=status,awsProperties,ontapClusterProperties
        api = '%s/working-environments/%s' % (rest_api.api_root_path, self.parameters['working_environment_id'])
        api += '?fields=status,providerProperties,ontapClusterProperties'
        response, error, dummy = rest_api.get(api, None, header=headers)
        if error:
            return None, error
        return response, None

    def compare_cvo_tags_labels(self, current_tags, user_tags, tag_name):
        '''
        Compare exiting tags/labels and user input tags/labels to see if there is a change
        gcp_labels: label_key, label_value
        aws_tag/azure_tag: tag_key, tag_label
        '''
        if len(user_tags) != len(current_tags):
            return True
        tag_label_prefix = 'tag' if tag_name != 'gcp_labels' else 'label'
        tkey = tag_label_prefix + '_key'
        tvalue = tag_label_prefix + '_value'
        # Check if tags/labels of desired configuration in current working environment
        for item in user_tags:
            if item[tkey] in current_tags and item[tvalue] != current_tags[item[tkey]]:
                return True
            elif item[tkey] not in current_tags:
                return True
        return False

    def is_cvo_tags_changed(self, rest_api, headers, parameters, tag_name):
        '''
        Since tags/laabels are CVO optional parameters, this function needs to cover with/without tags/labels on both lists
        '''
        # get working environment details by working environment ID
        current, error = self.get_working_environment_details(rest_api, headers)
        if error is not None:
            return 'Error:  Cannot find working environment %s error: %s' % (self.parameters['working_environment_id'], str(error))
        self.set_api_root_path(current, rest_api)
        # compare tags
        # no tags in current cvo
        if 'userTags' not in current:
            return tag_name in parameters

        # no tags in input parameters
        if tag_name not in parameters:
            return True
        else:
            # has tags in input parameters and existing CVO
            return self.compare_cvo_tags_labels(current['userTags'], parameters[tag_name], tag_name)

    def get_modify_cvo_params(self, rest_api, headers, desired, provider):
        modified = ['svm_password']
        # Get current working environment property
        we, err = self.get_working_environment_property(rest_api, headers)
        tier_level = we['ontapClusterProperties']['capacityTierInfo']['tierLevel']

        # collect changed attributes
        if provider == 'azure':
            if desired['capacity_tier'] == 'Blob' and tier_level != desired['tier_level']:
                modified.append('tier_level')
        else:
            if tier_level != desired['tier_level']:
                modified.append('tier_level')

        if provider == 'aws' and self.is_cvo_tags_changed(rest_api, headers, desired, 'aws_tag'):
            modified.append('aws_tag')
        if provider == 'azure' and self.is_cvo_tags_changed(rest_api, headers, desired, 'azure_tag'):
            modified.append('azure_tag')
        if provider == 'gcp' and self.is_cvo_tags_changed(rest_api, headers, desired, 'gcp_labels'):
            modified.append('gcp_labels')

        # The updates of followings are not supported. Will response failure.
        for key, value in desired.items():
            if key == 'project_id' and we['providerProperties']['projectName'] != value:
                modified.append('project_id')
            if key == 'zone' and we['providerProperties']['zoneName'][0] != value:
                modified.append('zone')
            if key == 'writing_speed_state' and we['ontapClusterProperties']['writingSpeedState'] is not None and \
                    we['ontapClusterProperties']['writingSpeedState'] != value:
                modified.append('writing_speed_state')
            if key == 'cidr' and we['providerProperties']['vnetCidr'] != value:
                modified.append('cidr')
            if key == 'location' and we['providerProperties']['regionName'] != value:
                modified.append('location')

        if modified:
            self.changed = True
        return modified

    def is_cvo_update_needed(self, rest_api, headers, parameters, changeable_params, provider):
        modify = self.get_modify_cvo_params(rest_api, headers, parameters, provider)
        unmodifiable = [attr for attr in modify if attr not in changeable_params]
        if len(unmodifiable) > 0:
            return None, "%s cannot be modified." % str(unmodifiable)
        else:
            return modify, None

    def update_cvo_tags(self, base_url, rest_api, headers, tag_name, tag_list):
        body = {}
        tags = []
        if tag_list is not None:
            for tag in tag_list:
                atag = {
                    'tagKey': tag['label_key'] if tag_name == "gcp_labels" else tag['tag_key'],
                    'tagValue': tag['label_value'] if tag_name == "gcp_labels" else tag['tag_value']
                }
                tags.append(atag)
        body['tags'] = tags

        response, err, dummy = rest_api.put(base_url + "user-tags", body, header=headers)
        if err is not None:
            return False, 'Error: unexpected response on modifying tags: %s, %s' % (str(err), str(response))
        else:
            return True, None

    def update_svm_password(self, base_url, rest_api, headers, svm_password):
        body = dict()
        body['password'] = svm_password
        response, err, dummy = rest_api.put(base_url + "set-password", body, header=headers)
        if err is not None:
            return False, 'Error: unexpected response on modifying svm_password: %s, %s' % (str(err), str(response))
        else:
            return True, None

    def update_tier_level(self, base_url, rest_api, headers, tier_level):
        body = dict()
        body['level'] = tier_level
        response, err, dummy = rest_api.post(base_url + "change-tier-level", body, header=headers)
        if err is not None:
            return False, 'Error: unexpected response on modify tier_level: %s, %s' % (str(err), str(response))
        else:
            return True, None
