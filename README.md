[![Documentation](https://img.shields.io/badge/docs-brightgreen.svg)](https://docs.ansible.com/ansible/devel/collections/netapp/cloudmanager/index.html)
![example workflow](https://github.com/ansible-collections/netapp.cloudmanager/actions/workflows/main.yml/badge.svg)
[![codecov](https://codecov.io/gh/ansible-collections/netapp.cloudmanager/branch/main/graph/badge.svg?token=weBYkksxSi)](https://codecov.io/gh/ansible-collections/netapp.cloudmanager)
# Ansible Collection - netapp.cloudmanager

Copyright (c) 2021 NetApp, Inc. All rights reserved.
Specifications subject to change without notice.

This collection requires python 3.5 or better.

# Installation
```bash
ansible-galaxy collection install netapp.cloudmanager
```
To use this collection, add the following to the top of your playbook:
```
collections:
  - netapp.cloudmanager
```
# Requirements
- ansible version >= 2.9
- requests >= 2.20

# Module documentation
https://docs.ansible.com/ansible/devel/collections/netapp/cloudmanager/

# Need help
Join our Slack Channel at [Netapp.io](http://netapp.io/slack)

# Code of Conduct
This collection follows the [Ansible project's Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).

# Documentation
https://github.com/ansible-collections/netapp/wiki

# Release Notes

## 21.11.0

## New Options
  - Adding new parameter `capacity_package_name` for all CVOs creation with capacity based license type capacity-paygo or ha-capacity-paygo for HA.

### Minor Changes
  - na_cloudmanager_connector_gcp - make the module idempotent for create and delete.
  - na_cloudmanager_connector_gcp - automatically fetch client_id for delete.
  - na_cloudmanager_connector_gcp - report client_id if connector already exists.
  - all modules - better error reporting if refresh_token is not valid.

### Bug Fixes
  - na_cloudmanager_connector_gcp - typeError when using proxy certificates.

## 21.10.0

### Minor Changes
  - Adding support update on `svm_password`, `tier_level`, `aws_tag`, `azure_tag` and `gcp_labels` for all CVOs. Only these parameters will be modified on the existing CVOs.

### Bug Fixes
  - na_cloudmanager_snapmirror - key error CloudProviderName for ONPREM operation

## New Options
  - Adding new parameter `ha_enable_https` for HA CVO to enable the HTTPS connection from CVO to storage accounts. This can impact write performance. The default is false.
  - Adding new parameters `kms_key_id` and `kms_key_arn` as AWS encryption parameters for AWS CVO encryption.
  - Adding new parameter `azure_encryption_parameters` for AZURE CVO encryption.
  - Adding new parameter `gcp_encryption_parameters` for GCP CVO encryption.

## 21.9.0

### New Options
  - Adding selflink support on CVO GCP params: `subnet_id`, `vpc0_node_and_data_connectivity`, `vpc1_cluster_connectivity`, `vpc2_ha_connectivity`, `vpc3_data_replication`, `subnet0_node_and_data_connectivity`, `subnet1_cluster_connectivity`, `subnet2_ha_connectivity`, and `subnet3_data_replication`.
  - Adding pd-balanced support on ``gcp_volume_type`` CVO GCP and ``provider_volume_type`` for na_cloudmanager_snapmirror and na_cloudmanager_volume.

### Bug Fixes
  - Change `virtual_machine_size` default value to Standard_DS3_v2

## 21.8.0

### New Options
  - Adding stage environment to all modules in cloudmanager
  - Adding service account support on API operations in cloudmanager: `sa_client_id` and `sa_secret_key`. `refresh_token` will be ignored if service account information is provided.

### Bug Fixes
  - Accept client_id end with or without 'clients'

## 21.7.0

### New Options
  - na_cloudmanager_cvo_aws: Support one new ebs_volume_type gp3
  - Adding stage environemt to all modules in cloudmanager
  - na_cloudmanager_volume: Add `aggregate_name` support on volume creation.
  - na_cloudmanager_cvo_aws: Support one new `ebs_volume_type` gp3
  - na_cloudmanager_connector_azure: Add `subnet_name` as aliases of `subnet_id`, `vnet_name` as aliases of `vnet_id`
  - na_cloudmanager_aggregate - Add provider_volume_type gp3 support.
  - na_cloudmanager_volume - Add provider_volume_type gp3 support.
  - na_cloudmanager_snapmirror - Add provider_volume_type gp3 support.
   
### Bug Fixes
  - na_cloudmanager_aggregate: Improve error message
  - na_cloudmanager_cvo_gcp: Apply `network_project_id` on vpc1_cluster_connectivity, vpc2_ha_connectivity, vpc3_data_replication, subnet1_cluster_connectivity, subnet2_ha_connectivity, subnet3_data_replication
  - na_cloudmanager_connector_gcp: rename option `service_account_email` and `service_account_path` to `gcp_service_account_email` and `gcp_service_account_path` respectively
  - na_cloudmanager_connector_azure: Fix KeyError client_id
  - na_cloudmanager_nss_account: Improve error message
  - na_cloudmanager_volume: Improve error message

## 21.6.0

### New Modules
  - na_cloudmanager_snapmirror: Create or Delete snapmirror on Cloud Manager

### Bug Fixes
  - na_cloudmanager_connector_gcp: Make client_id as optional
  - na_cloudmanager_cvo_gcp: Change vpc_id from optional to required.

## 21.5.1

### Bug fixes
  - na_cloudmanager_cifs_server: Fix incorrect API call when is_workgroup is true
  - na_cloudmanager_connector_azure: Fix python error - msrest.exceptions.ValidationError. Parameter 'Deployment.properties' can not be None.
  - na_cloudmanager_connector_azure: Fix wrong example on the document and update account_id is required field on deletion.

## 21.5.0

### New Options
  - na_cloudmanager_connector_aws: Return newly created Azure client ID in cloud manager, instance ID and account ID. New option `proxy_certificates`.
  - na_cloudmanager_cvo_aws: Return newly created AWS working_environment_id
  - na_cloudmanager_cvo_azure: Return newly created AZURE working_environment_id
  - na_cloudmanager_cvo_gcp: Return newly created GCP working_environment_id

## Bug Fixes
  - na_cloudmanager_cvo_aws: Fix incorrect placement of platformSerialNumber in the resulting json structure

## 21.4.0

### Module documentation changes
  - Remove the period at the end of the line on short_description
  - Add period at the end of the names in examples
  - Add notes mentioning support check_mode

### New Modules
  - na_cloudmanager_connector_azure: Create or delete Cloud Manager connector for Azure.
  - na_cloudmanager_cvo_azure: Create or delete Cloud Manager CVO for AZURE for both single and HA.
  - na_cloudmanager_info: Gather Cloud Manager subset information using REST APIs. Support for subsets `working_environments_info`, `aggregates_info`, `accounts_info`.
  - na_cloudmanager_connector_gcp: Create or delete Cloud Manager connector for GCP.
  - na_cloudmanager_cvo_gcp: Create or delete Cloud Manager CVO for GCP for both single and HA.

## 21.3.0

### New Modules
  - na_cloudmanager_aggregate: Create or delete an aggregate on Cloud Volumes ONTAP, or add disks on an aggregate.
  - na_cloudmanager_cifs_server: Create or delete CIFS server for Cloud Volumes ONTAP.
  - na_cloudmanager_connector_aws: Create or delete Cloud Manager connector for AWS.
  - na_cloudmanager_cvo_aws: Create or delete Cloud Manager CVO for AWS for both single and HA.
  - na_cloudmanager_nss_account: Create or delete a nss account on Cloud Manager.
  - na_cloudmanager_volume: Create, modify or delete a volume on Cloud Volumes ONTAP.

