import logging
import os

from cloudbridge.cloud.base import BaseCloudProvider
from cloudbridge.cloud.interfaces import TestMockHelperMixin

from cloudbridge.cloud.providers.azure.azure_client import AzureClient
from cloudbridge.cloud.providers.azure.mock_azure_client import MockAzureClient
from cloudbridge.cloud.providers.azure.services import AzureSecurityService, AzureObjectStoreService

log = logging.getLogger(__name__)


class AzureCloudProvider(BaseCloudProvider):
    PROVIDER_ID = 'azure'

    def __init__(self, config, azureclient=None):
        super(AzureCloudProvider, self).__init__(config)
        self.cloud_type = 'azure'

        # mandatory config values
        self.subscription_id = self._get_config_value(
            'azure_subscription_id', os.environ.get('AZURE_SUBSCRIPTION_ID', None))
        self.client_Id = self._get_config_value(
            'azure_client_Id', os.environ.get('AZURE_CLIENT_ID', None))
        self.secret = self._get_config_value(
            'azure_secret', os.environ.get('AZURE_SECRET', None))
        self.tenant = self._get_config_value(
            'azure_tenant', os.environ.get('AZURE_TENANT', None))

        # optional config values
        self.region_name = self._get_config_value(
            'azure_region_name', os.environ.get('AZURE_REGION_NAME', 'eastus'))
        self.resource_group = self._get_config_value(
            'azure_resource_group', os.environ.get('AZURE_RESOURCE_GROUP', 'cloudbridge-azure'))

        self.storage_account_name = self._get_config_value(
            'azure_storage_account_name', os.environ.get('AZURE_STORAGE_ACCOUNT_NAME', 'cloudbridgeazure'))

        # create a dict with both optional and mandatory configuration values to pass to the azureclient class, rather
        # than passing the provider object and taking a dependency.

        self.allconfig ={'azure_subscription_id': self.subscription_id,
                         'azure_client_Id':  self.client_Id,
                         'azure_secret': self.secret,
                         'azure_tenant': self.tenant,
                         'azure_region_name': self.region_name,
                         'azure_resource_group':  self.resource_group,
                         'azure_storage_account_name' : self.storage_account_name
                         }

        # TODO: implement code to validate if the resource group is available,if not create
        self._azure_client = azureclient or AzureClient(self.allconfig)

        self._security = AzureSecurityService(self)
        self._object_store = AzureObjectStoreService(self)

    @property
    def compute(self):
        raise NotImplementedError(
            "AzureCloudProvider does not implement this service")

    @property
    def network(self):
        return self._security

    @property
    def security(self):
        raise NotImplementedError(
            "AzureCloudProvider does not implement this service")

    @property
    def block_store(self):
        raise NotImplementedError(
            "AzureCloudProvider does not implement this service")

    @property
    def object_store(self):
        return self._object_store

    @property
    def azure_client(self):
        return self._azure_client


class MockAzureCloudProvider(AzureCloudProvider, TestMockHelperMixin):
    def __init__(self, config):
        super(MockAzureCloudProvider, self).__init__(config, MockAzureClient(self))

    def setUpMock(self):
        pass

    def tearDownMock(self):
        pass

