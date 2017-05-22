import azure_integration_test.helpers as helpers

from azure_integration_test.helpers import ProviderTestBase


class AzureIntegrationImageServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['compute.images'])
    def test_azure_image_service(self):
        images_list = self.provider.compute.images.list()

        if images_list.total_results > 0:
            found_images_list = self.provider.compute.images.\
                find(images_list[0].name[:2])
            print("Find Images  count - {0}".
                  format(str(found_images_list.total_results)))
            self.assertTrue(found_images_list.total_results > 0)
            image_get = self.provider.compute.images.get(images_list[0].id)
            print("Get Image - " + str(image_get))
            self.assertIsNotNone(image_get)

        image_get.delete()
        image_get_after_delete = self.provider.compute.images.get(image_get.id)
        print("Get Image - " + str(image_get_after_delete))
        self.assertIsNone(image_get_after_delete)
