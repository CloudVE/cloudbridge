import logging
from io import BytesIO

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlockBlobService

log = logging.getLogger(__name__)


class AzureClient(object):
    def __init__(self, config):
        self._config = config
        self.subscription_id = config.get('azure_subscription_id')
        credentials = ServicePrincipalCredentials(
            client_id=config.get('azure_client_Id'),
            secret=config.get('azure_secret'),
            tenant=config.get('azure_tenant')
        )

        self._resource_client = ResourceManagementClient(credentials,
                                                         self.subscription_id)
        self._storage_client = StorageManagementClient(credentials,
                                                       self.subscription_id)
        self._network_management_client = NetworkManagementClient(
            credentials, self.subscription_id)
        self._subscription_client = SubscriptionClient(credentials)
        self._compute_client = ComputeManagementClient(credentials,
                                                       self.subscription_id)

        self._access_key_result = None
        self._block_blob_service = None

        log.debug("azure subscription : %s", self.subscription_id)

    @property
    def access_key_result(self):
        if not self._access_key_result:
            self._access_key_result = self.storage_client.storage_accounts. \
                list_keys(self.resource_group_name, self.storage_account_name)
        return self._access_key_result

    @property
    def resource_group_name(self):
        return self._config.get('azure_resource_group')

    @property
    def storage_account_name(self):
        return self._config.get('azure_storage_account_name')

    @property
    def region_name(self):
        return self._config.get('azure_region_name')

    @property
    def storage_client(self):
        return self._storage_client

    @property
    def subscription_client(self):
        return self._subscription_client

    @property
    def resource_client(self):
        return self._resource_client

    @property
    def compute_client(self):
        return self._compute_client

    @property
    def network_management_client(self):
        return self._network_management_client

    @property
    def blob_service(self):
        if not self._block_blob_service:
            self._block_blob_service = BlockBlobService(
                self.storage_account_name,
                self.access_key_result.keys[0].value)
        return self._block_blob_service

    def get_resource_group(self, name):
        return self.resource_client.resource_groups.get(name)

    def create_resource_group(self, name, parameters):
        return self.resource_client.resource_groups. \
            create_or_update(name, parameters)

    def get_storage_account(self, storage_account_name):
        return self.storage_client.storage_accounts. \
            get_properties(self.resource_group_name, storage_account_name)

    def create_storage_account(self, name, params):
        return self.storage_client.storage_accounts. \
            create(self.resource_group_name, name, params).result()

    def list_locations(self):
        return self.subscription_client.subscriptions. \
            list_locations(self.subscription_id)

    def list_security_group(self):
        return self.network_management_client.network_security_groups. \
            list(self.resource_group_name)

    def create_security_group(self, name, parameters):
        return self.network_management_client.network_security_groups. \
            create_or_update(self.resource_group_name, name,
                             parameters).result()

    def create_security_group_rule(self, security_group,
                                   rule_name, parameters):
        return self.network_management_client.security_rules. \
            create_or_update(self.resource_group_name, security_group,
                             rule_name, parameters).result()

    def delete_security_group_rule(self, name, security_group):
        return self.network_management_client.security_rules. \
            delete(self.resource_group_name, security_group, name).result()

    def get_security_group(self, name):
        return self.network_management_client.network_security_groups. \
            get(self.resource_group_name, name)

    def delete_security_group(self, name):
        delete_async = self.network_management_client \
            .network_security_groups. \
            delete(self.resource_group_name, name)
        delete_async.wait()

    def list_containers(self, prefix=None):
        return self.blob_service.list_containers(prefix=prefix)

    def create_container(self, container_name):
        self.blob_service.create_container(container_name)
        return self.blob_service.get_container_properties(container_name)

    def get_container(self, container_name):
        return self.blob_service.get_container_properties(container_name)

    def delete_container(self, container_name):
        self.blob_service.delete_container(container_name)

    def list_blobs(self, container_name, prefix=None):
        return self.blob_service.list_blobs(container_name, prefix=prefix)

    def get_blob(self, container_name, blob_name):
        return self.blob_service.get_blob_properties(container_name, blob_name)

    def create_blob_from_text(self, container_name, blob_name, text):
        self.blob_service.create_blob_from_text(container_name,
                                                blob_name, text)

    def create_blob_from_file(self, container_name, blob_name, file_path):
        self.blob_service.create_blob_from_path(container_name,
                                                blob_name, file_path)

    def delete_blob(self, container_name, blob_name):
        self.blob_service.delete_blob(container_name, blob_name)

    def get_blob_url(self, container_name, blob_name):
        return self.blob_service.make_blob_url(container_name, blob_name)

    def get_blob_content(self, container_name, blob_name):
        out_stream = BytesIO()
        self.blob_service.get_blob_to_stream(container_name,
                                             blob_name, out_stream)
        return out_stream

    def create_empty_disk(self, disk_name, size,
                          region=None, snapshot_id=None,
                          description=None):

        if snapshot_id:
            return self.create_snapshot_disk(disk_name,
                                             snapshot_id, region=region)

        params = {
            'location': region or self.region_name,
            'disk_size_gb': size,
            'creation_data': {
                'create_option': 'empty'
            }
        }
        if description:
            params['tags'] = {'Description': description}

        async_creation = self.compute_client.disks.create_or_update(
            self.resource_group_name,
            disk_name,
            params,
            raw=True
        )
        return async_creation

    def create_snapshot_disk(self, disk_name, snapshot_id, region=None):
        disk_response = self.compute_client.disks.create_or_update(
            self.resource_group_name,
            disk_name,
            {
                'location': region or self.region_name,
                'creation_data': {
                    'create_option': 'copy',
                    'source_uri': snapshot_id
                }
            },
            raw=True
        )

        return disk_response

    def update_disk_tags(self, disk_name, tags, region=None):
        disk_result = self.compute_client.disks.update(
            self.resource_group_name,
            disk_name,
            {
                'tags': tags
            },
            raw=True
        )
        return disk_result

    def get_disk(self, disk_name):
        return self.compute_client.disks. \
            get(self.resource_group_name, disk_name)

    def list_disks(self):
        return self.compute_client.disks. \
            list_by_resource_group(self.resource_group_name)

    def delete_disk(self, disk_name):
        async_deletion = self.compute_client.disks. \
            delete(self.resource_group_name, disk_name)
        async_deletion.wait()

    def attach_disk(self, vm_name, disk_name, disk_id):
        vm = self.compute_client.virtual_machines.get(
            self.resource_group_name,
            vm_name
        )

        if vm:
            vm.storage_profile.data_disks.append({
                'lun': len(vm.storage_profile.data_disks),
                'name': disk_name,
                'create_option': 'attach',
                'managed_disk': {
                    'id': disk_id
                }
            })
            self.compute_client.virtual_machines.create_or_update(
                self.resource_group_name,
                vm.name,
                vm,
                raw=True
            )

    def detach_disk(self, disk_id):
        virtual_machine = None
        for index, vm in enumerate(
                self.compute_client.virtual_machines.list(
                    self.resource_group_name)):
            for index, item in enumerate(vm.storage_profile.data_disks):
                if item.managed_disk and item.managed_disk.id == disk_id:
                    vm.storage_profile.data_disks.remove(item)
                    virtual_machine = vm
                break

        if virtual_machine:
            self.compute_client.virtual_machines.create_or_update(
                self.resource_group_name,
                virtual_machine.name,
                virtual_machine,
                raw=True
            )