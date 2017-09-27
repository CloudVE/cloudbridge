from cloudbridge.cloud.providers.azure.integration_test import helpers
from cloudbridge.cloud.providers.azure. \
    integration_test.helpers import ProviderTestBase


class AzureIntegrationImageServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['compute.images'])
    def test_azure_image_service(self):
        images_list = self.provider.compute.images.list()
        print("Images List" + str(images_list))
        print("List count - " + str(len(images_list)))

        print(str(images_list[0].name))

        if images_list.total_results > 0:
            found_images_list = self.provider.compute.images. \
                find(images_list[0].name)
            print("Find Images  count - {0}".
                  format(str(found_images_list.total_results)))
            self.assertTrue(found_images_list.total_results > 0)
            image_get = self.provider.compute.images.get(images_list[0].id)
            print("Get Image - " + str(image_get))
            self.assertIsNotNone(image_get)

            # image_get.delete()

            image_get_after_delete = \
                self.provider.compute.images.get(image_get.id)
            print("Get Image - " + str(image_get_after_delete))
            self.assertIsNone(image_get_after_delete)

            images_list_after_delete = self.provider.compute.images.list()
            print("Images List after Delete" + str(images_list_after_delete))
            print("List count after Delete- "
                  + str(len(images_list_after_delete)))
