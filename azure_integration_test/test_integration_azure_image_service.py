import azure_integration_test.helpers as helpers

from azure_integration_test.helpers import ProviderTestBase


class AzureIntegrationImageServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_image_service(self):
        image_id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96" \
                   "/resourceGroups/cloudbridge-azure/providers" \
                   "/Microsoft.Compute/images/sampleImage"

        images_list = self.provider.compute.images.list()
        print("List image - " + str(images_list))
        self.assertEqual(len(images_list), 2)

        image_get = self.provider.compute.images.get(image_id)
        print("Get Image - " + str(image_get))
        self.assertIsNotNone(image_get)

        # print("Before updating tag - " + str(image_get.name))
        # image_get.name("NewTestImage")
        # print("After updating tag - " + str(image_get.name))
