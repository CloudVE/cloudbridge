import logging

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

        self._resource_client = ResourceManagementClient(credentials, self.subscription_id)
        self._storage_client = StorageManagementClient(credentials, self.subscription_id)
        self._network_management_client = NetworkManagementClient(credentials, self.subscription_id)
        self._subscription_client = SubscriptionClient(credentials)
        self._compute_client = ComputeManagementClient(credentials, self.subscription_id)

        log.debug("azure subscription : %s", self.subscription_id)

    @property
    def resource_group_name(self):
        return self._config.get('azure_resource_group')

    @property
    def storage_account_name(self):
        return self._config.get('azure_storage_account_name')

    @property
    def block_blob_service(self):
        return self._storage_client

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

    def list_locations(self):
        return self.subscription_client.subscriptions.list_locations(self.subscription_id)

    def list_security_group(self):
        return self.network_management_client.network_security_groups.list(self.resource_group_name)

    def get_security_group(self, name):
        return self.network_management_client.network_security_groups.get(self.resource_group_name, name)

    def list_containers(self):
        access_key_result = self.storage_client.storage_accounts.list_keys(self.resource_group_name, self.storage_account_name)
        block_blob_service = BlockBlobService(self.storage_account_name, access_key_result.keys[0].value)
        return block_blob_service.list_containers()

    def create_container(self, container_name):
        access_key_result = self.storage_client.storage_accounts.list_keys(self.resource_group_name, self.storage_account_name)
        block_blob_service = BlockBlobService(self.storage_account_name, access_key_result.keys[0].value)
        return block_blob_service.create_container(container_name)

    def get_container(self, container_name):
        access_key_result = self.storage_client.storage_accounts.list_keys(self.resource_group_name, self.storage_account_name)
        block_blob_service = BlockBlobService(self.storage_account_name, access_key_result.keys[0].value)
        return block_blob_service.get_container_properties(container_name)

    def delete_container(self, container_name):
        access_key_result = self.storage_client.storage_accounts.list_keys(self.resource_group_name, self.storage_account_name)
        block_blob_service = BlockBlobService(self.storage_account_name, access_key_result.keys[0].value)
        block_blob_service.delete_container(container_name)
        return None
