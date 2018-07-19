import logging
import os

from cloudbridge.cloud.base import BaseCloudProvider
from cloudbridge.cloud.providers.azure.azure_client import AzureClient
from cloudbridge.cloud.providers.azure.services \
    import AzureComputeService, AzureNetworkingService, \
    AzureSecurityService, AzureStorageService

from msrestazure.azure_exceptions import CloudError

import tenacity

log = logging.getLogger(__name__)


class AzureCloudProvider(BaseCloudProvider):
    PROVIDER_ID = 'azure'

    def __init__(self, config):
        super(AzureCloudProvider, self).__init__(config)

        # mandatory config values
        self.subscription_id = self. \
            _get_config_value('azure_subscription_id',
                              os.environ.get('AZURE_SUBSCRIPTION_ID', None))
        self.client_id = self._get_config_value(
            'azure_client_id', os.environ.get('AZURE_CLIENT_ID', None))
        self.secret = self._get_config_value(
            'azure_secret', os.environ.get('AZURE_SECRET', None))
        self.tenant = self._get_config_value(
            'azure_tenant', os.environ.get('AZURE_TENANT', None))

        # optional config values
        self.region_name = self._get_config_value(
            'azure_region_name', os.environ.get('AZURE_REGION_NAME',
                                                'northcentralus'))
        self.resource_group = self._get_config_value(
            'azure_resource_group', os.environ.get('AZURE_RESOURCE_GROUP',
                                                   'cloudbridge'))
        # Storage account name is limited to a max length of 24 characters
        # so take part of the client id to keep it unique
        self.storage_account = self._get_config_value(
            'azure_storage_account',
            os.environ.get('AZURE_STORAGE_ACCOUNT',
                           'storageacc' + self.client_id[-12:]))

        self.vm_default_user_name = self._get_config_value(
            'azure_vm_default_user_name', os.environ.get
            ('AZURE_VM_DEFAULT_USER_NAME', 'cbuser'))

        self.public_key_storage_table_name = self._get_config_value(
            'azure_public_key_storage_table_name', os.environ.get
            ('AZURE_PUBLIC_KEY_STORAGE_TABLE_NAME', 'cbcerts'))

        self._azure_client = None

        self._security = AzureSecurityService(self)
        self._storage = AzureStorageService(self)
        self._compute = AzureComputeService(self)
        self._networking = AzureNetworkingService(self)

    @property
    def compute(self):
        return self._compute

    @property
    def networking(self):
        return self._networking

    @property
    def security(self):
        return self._security

    @property
    def storage(self):
        return self._storage

    @property
    def azure_client(self):
        if not self._azure_client:

            # create a dict with both optional and mandatory configuration
            # values to pass to the azureclient class, rather
            # than passing the provider object and taking a dependency.

            provider_config = {
                'azure_subscription_id': self.subscription_id,
                'azure_client_id': self.client_id,
                'azure_secret': self.secret,
                'azure_tenant': self.tenant,
                'azure_region_name': self.region_name,
                'azure_resource_group': self.resource_group,
                'azure_storage_account': self.storage_account,
                'azure_public_key_storage_table_name':
                    self.public_key_storage_table_name
            }

            self._azure_client = AzureClient(provider_config)
            self._initialize()
        return self._azure_client

    def _initialize(self):
        """
        Verifying that resource group and storage account exists
        if not create one with the name provided in the
        configuration
        """
        try:
            self._azure_client.get_resource_group(self.resource_group)
        except CloudError:
            resource_group_params = {'location': self.region_name}
            self._azure_client.create_resource_group(self.resource_group,
                                                     resource_group_params)
        # Create a storage account. To prevent a race condition, try
        # to get or create at least twice
        self._get_or_create_storage_account()

    @tenacity.retry(stop=tenacity.stop_after_attempt(2))
    def _get_or_create_storage_account(self):
        try:
            return self._azure_client.get_storage_account(self.storage_account)
        except CloudError:
            storage_account_params = {
                'sku': {
                    'name': 'Standard_LRS'
                },
                'kind': 'storage',
                'location': self.region_name,
            }
            self._azure_client.create_storage_account(self.storage_account,
                                                      storage_account_params)
