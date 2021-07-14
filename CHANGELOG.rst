============================================
NetApp CloudManager Collection Release Notes
============================================

.. contents:: Topics


v21.8.0
=======

Major Changes
-------------

- Adding stage environment to all modules in cloudmanager

Minor Changes
-------------

- na_cloudmanager - Support service account with new options ``sa_client_id`` and ``sa_secret_key`` to use for API operations.

Bugfixes
--------

- na_cloudmanager_aggregate - accept client_id end with or without 'clients'
- na_cloudmanager_cifs_server - accept client_id end with or without 'clients'
- na_cloudmanager_connector_aws - accept client_id end with or without 'clients'
- na_cloudmanager_connector_azure - accept client_id end with or without 'clients'
- na_cloudmanager_connector_gcp - accept client_id end with or without 'clients'
- na_cloudmanager_cvo_aws - accept client_id end with or without 'clients'
- na_cloudmanager_cvo_azure - accept client_id end with or without 'clients'
- na_cloudmanager_cvo_gcp - accept client_id end with or without 'clients'
- na_cloudmanager_info - accept client_id end with or without 'clients'
- na_cloudmanager_nss_account - accept client_id end with or without 'clients'
- na_cloudmanager_snapmirror - accept client_id end with or without 'clients'
- na_cloudmanager_volume - accept client_id end with or without 'clients'

v21.7.0
=======

Minor Changes
-------------

- na_cloudmanager_aggregate - Add provider_volume_type gp3 support.
- na_cloudmanager_connector_gcp - rename option ``service_account_email`` and ``service_account_path`` to ``gcp_service_account_email`` and ``gcp_service_account_path`` respectively.
- na_cloudmanager_cvo_aws - Add ebs_volume_type gp3 support.
- na_cloudmanager_snapmirror - Add provider_volume_type gp3 support.
- na_cloudmanager_volume - Add aggregate_name support on volume creation.
- na_cloudmanager_volume - Add provider_volume_type gp3 support.

Bugfixes
--------

- na_cloudmanager_aggregate - Improve error message
- na_cloudmanager_connector_azure - Add subnet_name as aliases of subnet_id, vnet_name as aliases of vnet_id.
- na_cloudmanager_connector_azure - Fix KeyError client_id
- na_cloudmanager_cvo_gcp - Apply network_project_id check on vpc1_cluster_connectivity, vpc2_ha_connectivity, vpc3_data_replication, subnet1_cluster_connectivity, subnet2_ha_connectivity, subnet3_data_replication
- na_cloudmanager_nss_account - Improve error message
- na_cloudmanager_volume - Improve error message

v21.6.0
=======

Bugfixes
--------

- na_cloudmanager_cifs_server - Fix incorrect API call when is_workgroup is true
- na_cloudmanager_connector_azure - Change client_id as optional
- na_cloudmanager_connector_azure - Fix python error - msrest.exceptions.ValidationError. Parameter 'Deployment.properties' can not be None.
- na_cloudmanager_connector_azure - Fix wrong example on the document and update account_id is required field on deletion.
- na_cloudmanager_cvo_gcp - Change vpc_id from optional to required.

New Modules
-----------

- netapp.cloudmanager.na_cloudmanager_snapmirror - NetApp Cloud Manager SnapMirror

v21.5.0
=======

Minor Changes
-------------

- na_cloudmanager_connector_aws - Return newly created Azure client ID in cloud manager, instance ID and account ID. New option ``proxy_certificates``.
- na_cloudmanager_cvo_aws - Return newly created AWS working_environment_id.
- na_cloudmanager_cvo_azure - Return newly created AZURE working_environment_id.
- na_cloudmanager_cvo_gcp - Return newly created GCP working_environment_id.

Bugfixes
--------

- na_cloudmanager_cvo_aws - Fix incorrect placement of platformSerialNumber in the resulting json structure

v21.4.0
=======

New Modules
-----------

- netapp.cloudmanager.na_cloudmanager_connector_azure - NetApp Cloud Manager connector for Azure.
- netapp.cloudmanager.na_cloudmanager_connector_gcp - NetApp Cloud Manager connector for GCP.
- netapp.cloudmanager.na_cloudmanager_cvo_azure - NetApp Cloud Manager CVO/working environment in single or HA mode for Azure.
- netapp.cloudmanager.na_cloudmanager_info - NetApp Cloud Manager info

v21.3.0
=======

New Modules
-----------

- netapp.cloudmanager.na_cloudmanager_aggregate - NetApp Cloud Manager Aggregate
- netapp.cloudmanager.na_cloudmanager_cifs_server - NetApp Cloud Manager cifs server
- netapp.cloudmanager.na_cloudmanager_connector_aws - NetApp Cloud Manager connector for AWS
- netapp.cloudmanager.na_cloudmanager_cvo_aws - NetApp Cloud Manager CVO for AWS
- netapp.cloudmanager.na_cloudmanager_nss_account - NetApp Cloud Manager nss account
- netapp.cloudmanager.na_cloudmanager_volume - NetApp Cloud Manager volume
