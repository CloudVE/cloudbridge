from cloudbridge.cloud.providers.azure.test.helpers import ProviderTestBase


class AzureStorageAccountTestCase(ProviderTestBase):
    def test_storage_account_create(self):
        storage_account_params = {
            'sku': {
                'name': 'Standard_LRS'
            },
            'kind': 'storage',
            'location': 'eastus',
        }
        rg = self.provider.azure_client. \
            create_storage_account('cloudbridgeazure',
                                   storage_account_params)
        print("Create Resource - " + str(rg))
        self.assertTrue(
            rg.name == "cloudbridgeazure",
            "Storage account name should be cloudbridgeazure")

    def test_storage_account_get(self):
        sa = self.provider.azure_client.get_storage_account('MyGroup')
        self.assertTrue(
            sa.name == "MyGroup",
            "storage account should be MyGroup")
