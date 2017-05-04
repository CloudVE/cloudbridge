import azure_test.helpers as helpers
from azure_test.helpers import ProviderTestBase


class AzureImageServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_images_list(self):
        images_list = self.provider.compute.images.list()
        print("List Images - " + str(images_list))
        self.assertEqual(len(images_list), 2)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_images_get_exist(self):
        image1_id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                    'resourceGroups/CLOUDBRIDGE-AZURE/providers/' \
                    'Microsoft.Compute/images/image1'
        image_get = self.provider.compute.images.get(image1_id)
        print("Get Image Exist - " + str(image_get))
        self.assertIsNotNone(image_get)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_images_get_notExist(self):
        image1_id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                    'resourceGroups/CLOUDBRIDGE-AZURE/providers/' \
                    'Microsoft.Compute/images/imageNotExist'
        image_get = self.provider.compute.images.get(image1_id)
        print("Get Image Not Exist- " + str(image_get))
        self.assertIsNone(image_get)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_images_find(self):
        image1_name = 'image1'
        with self.assertRaises(NotImplementedError):
            image_find = self.provider.compute.images \
                .find(image1_name)
            print("Find Image  - " + str(image_find))
            self.assertEqual(
                len(image_find), 1)
