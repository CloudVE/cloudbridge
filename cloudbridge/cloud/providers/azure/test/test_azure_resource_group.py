from cloudbridge.cloud.providers.azure.test.helpers import ProviderTestBase


class AzureResourceGroupTestCase(ProviderTestBase):
    def test_resource_group_create(self):
        resource_group_params = {'location': self.provider.region_name}
        rg = self.provider.azure_client. \
            create_resource_group(self.provider.resource_group,
                                  resource_group_params)
        print("Create Resource - " + str(rg))
        self.assertTrue(
            rg.name == self.provider.resource_group,
            "Resource Group should be {0}".format(rg.name))

    def test_resource_group_get(self):
        rg = self.provider.azure_client.get_resource_group('MyGroup')
        print("Get Resource - " + str(rg))
        self.assertTrue(
            rg.name == "testResourceGroup",
            "Resource Group should be {0}".format(rg.name))
