import logging
import uuid

from msrestazure.azure_exceptions import CloudError

import tenacity

from cloudbridge.cloud.base import BaseCloudProvider
from cloudbridge.cloud.base.helpers import get_env
from cloudbridge.cloud.interfaces.exceptions import ProviderConnectionException
from cloudbridge.cloud.providers.azure.azure_client import AzureClient
from cloudbridge.cloud.providers.azure.services \
    import AzureComputeService, AzureNetworkingService, \
    AzureSecurityService, AzureStorageService

log = logging.getLogger(__name__)


class AzureCloudProvider(BaseCloudProvider):
    PROVIDER_ID = 'azure'

    def __init__(self, config):
        super(AzureCloudProvider, self).__init__(config)

        # mandatory config values
        self.subscription_id = self._get_config_value(
            'azure_subscription_id', get_env('AZURE_SUBSCRIPTION_ID'))
        self.client_id = self._get_config_value(
            'azure_client_id', get_env('AZURE_CLIENT_ID', None))
        self.secret = self._get_config_value(
            'azure_secret', get_env('AZURE_SECRET', None))
        self.tenant = self._get_config_value(
            'azure_tenant', get_env('AZURE_TENANT', None))

        # optional config values
        self.access_token = self._get_config_value(
            'azure_access_token', get_env('AZURE_ACCESS_TOKEN', None))
        self.region_name = self._get_config_value(
            'azure_region_name', get_env('AZURE_REGION_NAME', 'eastus'))
        self.resource_group = self._get_config_value(
            'azure_resource_group', get_env('AZURE_RESOURCE_GROUP',
                                            'cloudbridge'))
        # Storage account name is limited to a max length of 24 alphanum chars
        # and unique across all of Azure. Thus, a uuid is used to generate a
        # unique name for the Storage Account based on the resource group,
        # while also using the subscription ID to ensure that different users
        # having the same resource group name do not have the same SA name.
        self.storage_account = self._get_config_value(
            'azure_storage_account',
            get_env(
                'AZURE_STORAGE_ACCOUNT',
                'storacc' + self.subscription_id[-6:] +
                str(uuid.uuid5(uuid.NAMESPACE_OID,
                               str(self.resource_group)))[-6:]))

        self.vm_default_user_name = self._get_config_value(
            'azure_vm_default_user_name', get_env(
                'AZURE_VM_DEFAULT_USER_NAME', 'cbuser'))

        self.public_key_storage_table_name = self._get_config_value(
            'azure_public_key_storage_table_name', get_env(
                'AZURE_PUBLIC_KEY_STORAGE_TABLE_NAME', 'cbcerts'))

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
                    self.public_key_storage_table_name,
                'azure_access_token': self.access_token
            }

            self._azure_client = AzureClient(provider_config)
            self._initialize()
        return self._azure_client

    @tenacity.retry(stop=tenacity.stop_after_attempt(2),
                    retry=tenacity.retry_if_exception_type(CloudError),
                    reraise=True)
    def _initialize(self):
        """
        Verifying that resource group and storage account exists
        if not create one with the name provided in the
        configuration
        """
        try:
            self._azure_client.get_resource_group(self.resource_group)

        except CloudError as cloud_error:
            if cloud_error.error.error == "ResourceGroupNotFound":
                resource_group_params = {'location': self.region_name}
                try:
                    self._azure_client.\
                        create_resource_group(self.resource_group,
                                              resource_group_params)
                except CloudError as cloud_error2:  # pragma: no cover
                    if cloud_error2.error.error == "AuthorizationFailed":
                        mess = 'The following error was returned by Azure:\n' \
                               '%s\n\nThis is likely because the Role' \
                               'associated with the given credentials does ' \
                               'not allow for Resource Group creation.\nA ' \
                               'Resource Group is necessary to manage ' \
                               'resources in Azure. You must either ' \
                               'provide an existing Resource Group as part ' \
                               'of the configuration, or elevate the ' \
                               'associated role.\nFor more information on ' \
                               'roles, see: https://docs.microsoft.com/' \
                               'en-us/azure/role-based-access-control/' \
                               'overview\n' % cloud_error2
                        raise ProviderConnectionException(mess)
                    else:
                        raise cloud_error2

            else:
                raise cloud_error
